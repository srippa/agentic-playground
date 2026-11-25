"""Offline deterministic unit tests for Stage 0 Part 0.1 (`config.py` and `cli.py`)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from rich.console import Console

from harness_lab import __version__
from harness_lab.cli import main
from harness_lab.config import (
    CloudProfileNotAllowedError,
    ConfigError,
    UnknownProfileError,
    find_repo_root,
    load_config,
)

REPO_ROOT = find_repo_root(Path(__file__).resolve())


def test_load_default_models_toml() -> None:
    cfg = load_config(REPO_ROOT / "models.toml")
    expected_profiles = {
        "workhorse",
        "bonsai-2.5",
        "alt-family",
        "fast",
        "chaos",
        "decision",
        "embed",
        "oracle",
    }
    assert set(cfg.profiles) == expected_profiles
    assert cfg.default_profile == "workhorse"
    assert cfg.profiles["workhorse"].model == "qwen3.8:27b"
    assert cfg.profiles["embed"].model == "embeddinggemma-2:270m"
    assert cfg.hardware.unified_memory_gb == 64.0
    assert cfg.hardware.safe_wired_ceiling_gb == 46.0
    assert cfg.hardware.max_loaded_models == 3


def test_get_profile_default_and_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = load_config(REPO_ROOT / "models.toml")
    monkeypatch.delenv("HARNESS_LAB_PROFILE", raising=False)
    assert cfg.get_profile().name == "workhorse"

    monkeypatch.setenv("HARNESS_LAB_PROFILE", "fast")
    assert cfg.get_profile().name == "fast"
    assert cfg.get_profile().api_key_placeholder() == "ollama"
    assert cfg.get_profile("bonsai-2.5").api_key_placeholder() == "lm-studio"


def test_unknown_profile_raises() -> None:
    cfg = load_config(REPO_ROOT / "models.toml")
    with pytest.raises(UnknownProfileError):
        cfg.get_profile("does-not-exist")


def test_cloud_oracle_blocked_by_default_and_requires_explicit_opt_in(
    tmp_path: Path,
) -> None:
    cfg = load_config(REPO_ROOT / "models.toml")
    with pytest.raises(CloudProfileNotAllowedError):
        cfg.get_profile("oracle")
    with pytest.raises(CloudProfileNotAllowedError):
        cfg.get_profile("oracle", allow_cloud=True)
    with pytest.raises(CloudProfileNotAllowedError):
        cfg.profiles["oracle"].api_key_placeholder()

    custom_toml = (REPO_ROOT / "models.toml").read_text(encoding="utf-8")
    enabled_toml = custom_toml.replace(
        "is_cloud = true\nenabled = false",
        "is_cloud = true\nenabled = true",
    )
    tmp_cfg_path = tmp_path / "models.toml"
    tmp_cfg_path.write_text(enabled_toml, encoding="utf-8")

    enabled_cfg = load_config(tmp_cfg_path)
    with pytest.raises(CloudProfileNotAllowedError):
        enabled_cfg.get_profile("oracle", allow_cloud=False)
    oracle = enabled_cfg.get_profile("oracle", allow_cloud=True)
    assert oracle.is_cloud is True
    assert oracle.enabled is True


def test_local_base_url_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:22434")
    monkeypatch.setenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:2234/v1/")
    cfg = load_config(REPO_ROOT / "models.toml")

    assert cfg.profiles["workhorse"].base_url == "http://127.0.0.1:22434/v1"
    assert cfg.profiles["workhorse"].native_base_url == "http://127.0.0.1:22434"
    assert cfg.profiles["bonsai-2.5"].base_url == "http://127.0.0.1:2234/v1"
    assert cfg.profiles["oracle"].base_url == "https://api.openai.com/v1"


def test_coresidency_budget_within_and_over_limits() -> None:
    cfg = load_config(REPO_ROOT / "models.toml")

    default_report = cfg.check_coresidency()
    assert default_report.total_est_ram_gb == 29.0
    assert default_report.within_budget is True
    assert default_report.model_count == 3
    assert default_report.within_slot_limit is True
    assert default_report.ok is True

    over_slots = cfg.check_coresidency(["workhorse", "alt-family", "fast", "chaos"])
    assert over_slots.model_count == 4
    assert over_slots.within_slot_limit is False
    assert over_slots.ok is False

    over_ram = cfg.check_coresidency(["workhorse", "alt-family", "bonsai-2.5", "fast"])
    assert over_ram.total_est_ram_gb == 54.0
    assert over_ram.within_budget is False
    assert over_ram.ok is False


def test_extra_toml_field_rejected(tmp_path: Path) -> None:
    base = (REPO_ROOT / "models.toml").read_text(encoding="utf-8")
    bad = base.replace('model = "qwen3.8:27b"', 'model = "qwen3.8:27b"\nunknown_key = 123', 1)
    bad_path = tmp_path / "bad_models.toml"
    bad_path.write_text(bad, encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(bad_path)


def test_cli_profiles_and_version() -> None:
    rec_console = Console(record=True, width=120)
    assert main(["version"], console=rec_console) == 0
    assert f"harness-lab {__version__}" in rec_console.export_text()

    prof_console = Console(record=True, width=120)
    assert main(["profiles"], console=prof_console) == 0
    output = prof_console.export_text()
    assert "qwen3.8:27b" in output
    assert "embeddinggemma-2:270m" in output
    assert "29.0 GB / 46.0 GB" in output
    assert "OK" in output

    err_console = Console(record=True, width=120)
    assert main(["profiles", "--coresident", "workhorse,nope"], console=err_console) == 2
    assert "Config error" in err_console.export_text()


def test_track_a_no_pydantic_ai_imports() -> None:
    for rel_path in ("src/harness_lab/config.py", "src/harness_lab/cli.py"):
        tree = ast.parse((REPO_ROOT / rel_path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("pydantic_ai")
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("pydantic_ai")
