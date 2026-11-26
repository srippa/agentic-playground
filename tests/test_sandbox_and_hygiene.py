"""Offline deterministic unit tests for Stage 0 Part 0.4 (sandbox & test hygiene)."""

from __future__ import annotations

import ast
import asyncio
from pathlib import Path

import pytest

from harness_lab.config import find_repo_root, load_config
from harness_lab.core.sandbox import (
    SandboxViolationError,
    get_sandbox_root,
    resolve_sandbox_path,
    sandbox_db_path,
    sandbox_tool_outputs_dir,
)
from harness_lab.stages.s00_foundations.run import run_doctor

REPO_ROOT = find_repo_root(Path(__file__).resolve())


def test_valid_nested_sandbox_paths_resolve(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox_data"
    sandbox.mkdir()
    sample = sandbox / "notes" / "trip.txt"
    sample.parent.mkdir(parents=True)
    sample.write_text("hello", encoding="utf-8")

    resolved_existing = resolve_sandbox_path(
        "notes/trip.txt",
        sandbox_root=sandbox,
        must_exist=True,
    )
    assert resolved_existing == sample.resolve()

    resolved_new = resolve_sandbox_path("sub/new.txt", sandbox_root=sandbox)
    assert resolved_new == (sandbox / "sub" / "new.txt").resolve()

    resolved_root = resolve_sandbox_path(".", sandbox_root=sandbox, allow_root=True)
    assert resolved_root == sandbox.resolve()

    assert get_sandbox_root(REPO_ROOT) == (REPO_ROOT / "sandbox_data").resolve()


def test_blocks_traversal_absolute_prefix_and_null_bytes(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox_data"
    sibling = tmp_path / "sandbox_data_evil"
    sandbox.mkdir()
    sibling.mkdir()

    bad_inputs = (
        "../pyproject.toml",
        "sub/../../outside.txt",
        "/etc/passwd",
        str(sibling / "secret.txt"),
        "../sandbox_data_evil/secret.txt",
        "bad\x00path.txt",
        "",
        ".",
    )
    for bad in bad_inputs:
        with pytest.raises(SandboxViolationError):
            resolve_sandbox_path(bad, sandbox_root=sandbox)


def test_blocks_symlink_escape_outside_sandbox(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox_data"
    outside_dir = tmp_path / "outside"
    sandbox.mkdir()
    outside_dir.mkdir()
    outside_file = outside_dir / "secret.txt"
    outside_file.write_text("top-secret", encoding="utf-8")

    file_link = sandbox / "escape.txt"
    file_link.symlink_to(outside_file)
    with pytest.raises(SandboxViolationError):
        resolve_sandbox_path("escape.txt", sandbox_root=sandbox)

    dir_link = sandbox / "dir_link"
    dir_link.symlink_to(outside_dir)
    with pytest.raises(SandboxViolationError):
        resolve_sandbox_path("dir_link/new.txt", sandbox_root=sandbox)


def test_blocks_protected_files_inside_sandbox(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox_data"
    sandbox.mkdir()
    for protected in (
        "AGENTS.md",
        "agents.md",
        ".env",
        ".env.local",
        "nested/.env.prod",
        "certs/private.pem",
        "api.key",
    ):
        with pytest.raises(SandboxViolationError):
            resolve_sandbox_path(protected, sandbox_root=sandbox)


def test_sandbox_db_and_tool_outputs_helpers(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox_data"
    sandbox.mkdir()

    db_path = sandbox_db_path("memory.db", sandbox_root=sandbox)
    assert db_path == (sandbox / "memory.db").resolve()

    for bad_db in ("../evil.db", "sub/a.db", "not_a_db.txt", ".env"):
        with pytest.raises(SandboxViolationError):
            sandbox_db_path(bad_db, sandbox_root=sandbox)

    spills = sandbox_tool_outputs_dir(sandbox_root=sandbox, create=True)
    assert spills == (sandbox / ".tool_outputs").resolve()
    assert spills.is_dir()


def test_gitignore_covers_lab_runtime_artifacts() -> None:
    lines = {
        line.strip()
        for line in (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    for required in (
        ".env",
        "traces/",
        "sandbox_data/.tool_outputs/",
        "sandbox_data/*.db",
        "benchmarks/results/",
    ):
        assert required in lines


def _is_track_a_module(rel_path: Path) -> bool:
    posix = rel_path.as_posix()
    if posix in {"__init__.py", "config.py", "cli.py"}:
        return True
    if posix.startswith(("core/", "stages/s00_foundations/")):
        return True
    return rel_path.name.startswith("track_a_")


def test_track_a_isolation_and_safety_ast_hygiene() -> None:
    src_root = REPO_ROOT / "src" / "harness_lab"
    py_files = sorted(src_root.rglob("*.py"))
    assert py_files
    for py_file in py_files:
        rel_path = py_file.relative_to(src_root)
        enforce_no_pydantic_ai = _is_track_a_module(rel_path)
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if enforce_no_pydantic_ai and isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("pydantic_ai"), str(py_file)
            elif enforce_no_pydantic_ai and isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("pydantic_ai"), str(py_file)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
                    raise AssertionError(f"Disallowed {node.func.id}() in {py_file}")
                for kw in node.keywords:
                    if (
                        kw.arg == "shell"
                        and isinstance(kw.value, ast.Constant)
                        and kw.value.value is True
                    ):
                        raise AssertionError(f"Disallowed shell=True in {py_file}")


@pytest.mark.live
def test_live_ollama_doctor_smoke(tmp_path: Path) -> None:
    """Live smoke test (deselected by default in `uv run pytest`)."""
    cfg = load_config(REPO_ROOT / "models.toml")
    report, _ = asyncio.run(run_doctor(cfg, traces_dir=tmp_path))
    assert report.ollama.reachable is True
