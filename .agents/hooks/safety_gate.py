#!/usr/bin/env python3
"""Deterministic PreToolUse safety gate for the agentic-playground workspace."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

PRIVATE_KEY_FILENAMES = {"id_rsa", "id_ed25519"}
PRIVATE_KEY_SUFFIXES = {".pem", ".key"}

SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(
        r"""\b(?:TYPESAFE_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY)\s*=\s*["']?([^\s"'#<>]{8,})["']?"""
    ),
]

DESTRUCTIVE_CMD_PATTERNS = [
    re.compile(r"\brm\s+-[^\n;|&]*r[^\n;|&]*f[^\n;|&]*\s+(/|~|\.\.)"),
    re.compile(r"\brm\s+-[^\n;|&]*f[^\n;|&]*r[^\n;|&]*\s+(/|~|\.\.)"),
    re.compile(r"\bsudo\b"),
    re.compile(r"\bmkfs\b"),
    re.compile(r"\bdd\s+if="),
    re.compile(r"(?:curl|wget)[^\n|]*\|\s*(?:sh|bash|zsh)\b"),
    re.compile(r"\b(?:cat|head|tail|less|more|sed|awk|grep)\s+[^\n]*\.env(?:\b|\.(?!example\b))"),
    re.compile(r"(?:^|[;&|]\s*)printenv(?:\s|$|[;&|])"),
]

FORCE_ASK_CMD_PATTERNS = [
    re.compile(r"\bollama\s+(?:pull|rm)\b"),
    re.compile(r"\buv\s+(?:add|python\s+install)\b"),
    re.compile(r"\bbrew\s+install\b"),
    re.compile(r"\bpip3?\s+install\b"),
    re.compile(r"\bnpm\s+install\b"),
    re.compile(r"\bgit\s+push\b"),
    re.compile(r"\bgit\s+reset\s+--hard\b"),
]


def _respond(decision: str, reason: str | None = None) -> None:
    payload: dict[str, Any] = {"decision": decision}
    if reason:
        payload["reason"] = reason
    print(json.dumps(payload))
    sys.exit(0)


def _extract_path(args: dict[str, Any]) -> str | None:
    for key in ("Path", "path", "TargetFile", "file_path"):
        val = args.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _resolve_path(raw_path: str, cwd: str | None, workspaces: list[str]) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        base = Path(cwd) if cwd else (Path(workspaces[0]) if workspaces else Path.cwd())
        candidate = base / candidate
    return candidate.resolve()


def _is_within_allowed_roots(resolved: Path, allowed_roots: list[Path]) -> bool:
    for root in allowed_roots:
        try:
            if resolved.is_relative_to(root):
                return True
        except ValueError:
            continue
    return False


def _is_env_secret_file(resolved: Path) -> bool:
    name = resolved.name
    if name == ".env.example":
        return False
    if name == ".env" or name.startswith(".env."):
        return True
    if name in PRIVATE_KEY_FILENAMES or resolved.suffix.lower() in PRIVATE_KEY_SUFFIXES:
        return True
    return False


def _is_hook_self_edit(resolved: Path, workspaces: list[Path]) -> bool:
    for ws in workspaces:
        hooks_json = (ws / ".agents" / "hooks.json").resolve()
        hooks_dir = (ws / ".agents" / "hooks").resolve()
        if resolved == hooks_json or resolved.is_relative_to(hooks_dir):
            return True
    return False


def _contains_secret(text: str) -> bool:
    for pattern in SECRET_PATTERNS:
        match = pattern.search(text)
        if match:
            if match.lastindex:
                val = match.group(1).lower()
                if any(tok in val for tok in ("placeholder", "example", "your_", "changeme")):
                    continue
            return True
    return False


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        _respond("ask", "safety_gate: could not parse hook payload")
        return

    tool_call = data.get("toolCall") or {}
    tool_name = str(tool_call.get("name") or "")
    args = tool_call.get("args") or {}
    if not isinstance(args, dict):
        args = {}

    cwd = data.get("cwd")
    workspace_strs = [p for p in (data.get("workspacePaths") or []) if isinstance(p, str)]
    workspaces = [Path(p).resolve() for p in workspace_strs]
    allowed_roots = list(workspaces)
    artifact_dir = data.get("artifactDirectoryPath")
    if isinstance(artifact_dir, str) and artifact_dir.strip():
        allowed_roots.append(Path(artifact_dir).resolve())

    if tool_name in {"read_file", "write_file", "edit_file"}:
        raw_path = _extract_path(args)
        if raw_path:
            resolved = _resolve_path(raw_path, cwd, workspace_strs)

            if _is_env_secret_file(resolved):
                _respond("deny", f"Access to secret/env file blocked: {resolved.name}")

            if tool_name in {"write_file", "edit_file"}:
                if allowed_roots and not _is_within_allowed_roots(resolved, allowed_roots):
                    _respond("deny", f"Write outside allowed workspace/artifact roots blocked: {resolved}")

                exempt_names = {".env.example", "safety_gate.py"}
                if resolved.name not in exempt_names:
                    text = str(args.get("Content") or args.get("Replacement") or "")
                    if text and _contains_secret(text):
                        _respond("deny", "Potential hardcoded API key or secret detected in file edit")

                if _is_hook_self_edit(resolved, workspaces):
                    _respond("force_ask", f"Modifying workspace safety hooks requires explicit approval: {resolved.name}")

    elif tool_name == "run_command":
        cmd = str(args.get("CommandLine") or "")
        for pattern in DESTRUCTIVE_CMD_PATTERNS:
            if pattern.search(cmd):
                _respond("deny", f"Blocked dangerous or secret-reading command matching {pattern.pattern}")

        if args.get("BypassSandbox") is True:
            _respond("force_ask", "Command requests BypassSandbox=true; confirm before running unsandboxed")

        for pattern in FORCE_ASK_CMD_PATTERNS:
            if pattern.search(cmd):
                _respond("force_ask", f"Command has large disk/network/remote impact ({pattern.pattern}); confirm")

    _respond("allow")


if __name__ == "__main__":
    main()
