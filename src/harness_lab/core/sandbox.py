"""Resolved-path `sandbox_data/` containment helpers (Track A stdlib-only)."""

from __future__ import annotations

from pathlib import Path

from harness_lab.config import find_repo_root

DEFAULT_SANDBOX_DIRNAME = "sandbox_data"
ALLOWED_DB_SUFFIXES: frozenset[str] = frozenset({".db", ".sqlite", ".sqlite3"})


class SandboxViolationError(PermissionError):
    """Raised when a path escapes `sandbox_data/` or targets a protected file."""


def get_sandbox_root(repo_root: Path | str | None = None) -> Path:
    """Return the resolved `sandbox_data/` root directory."""
    root = Path(repo_root).resolve() if repo_root is not None else find_repo_root()
    return (root / DEFAULT_SANDBOX_DIRNAME).resolve()


def _is_protected_path(resolved: Path, sandbox_root: Path) -> bool:
    rel = resolved.relative_to(sandbox_root)
    for part in rel.parts:
        low = part.lower()
        if (
            low == "agents.md"
            or low == ".env"
            or low.startswith(".env.")
            or low.endswith(".pem")
            or low.endswith(".key")
        ):
            return True
    return False


def resolve_sandbox_path(
    path: Path | str,
    *,
    sandbox_root: Path | str | None = None,
    must_exist: bool = False,
    allow_root: bool = False,
) -> Path:
    """Resolve `path` strictly inside `sandbox_data/`, blocking traversals and symlinks."""
    raw = str(path)
    if "\x00" in raw:
        raise SandboxViolationError("Null byte detected in sandbox path.")
    stripped = raw.strip()
    if not stripped or stripped == ".":
        if not allow_root:
            raise SandboxViolationError("Empty or root sandbox path requires allow_root=True.")
        candidate = Path(".")
    else:
        candidate = Path(stripped)

    root = (
        Path(sandbox_root).resolve()
        if sandbox_root is not None
        else get_sandbox_root()
    )
    target = candidate if candidate.is_absolute() else (root / candidate)
    resolved = target.resolve(strict=False)

    if not resolved.is_relative_to(root):
        raise SandboxViolationError(
            f"Path '{path}' resolves to '{resolved}', outside sandbox '{root}'."
        )
    if resolved == root and not allow_root:
        raise SandboxViolationError("Targeting the sandbox root directly is not permitted.")
    if _is_protected_path(resolved, root):
        raise SandboxViolationError(
            f"Access to protected policy or credential file '{resolved.name}' is blocked."
        )
    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"Sandbox path does not exist: {resolved}")
    return resolved


def sandbox_db_path(
    db_name: str,
    *,
    sandbox_root: Path | str | None = None,
) -> Path:
    """Return a validated SQLite database path directly inside `sandbox_data/`."""
    clean = db_name.strip()
    if not clean or "/" in clean or "\\" in clean:
        raise SandboxViolationError(
            f"Database name '{db_name}' must be a plain filename without directory separators."
        )
    if Path(clean).suffix.lower() not in ALLOWED_DB_SUFFIXES:
        allowed = ", ".join(sorted(ALLOWED_DB_SUFFIXES))
        raise SandboxViolationError(
            f"Database name '{db_name}' must end with one of: {allowed}."
        )
    return resolve_sandbox_path(clean, sandbox_root=sandbox_root)


def sandbox_tool_outputs_dir(
    *,
    sandbox_root: Path | str | None = None,
    create: bool = False,
) -> Path:
    """Return the resolved `sandbox_data/.tool_outputs/` artifact-spill directory."""
    out_dir = resolve_sandbox_path(".tool_outputs", sandbox_root=sandbox_root)
    if create:
        out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir
