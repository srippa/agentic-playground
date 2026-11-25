#!/usr/bin/env python3
"""PostToolUse hygiene hook: runs ruff check (to stderr) on edited Python files."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _extract_path(args: dict[str, Any]) -> str | None:
    for key in ("Path", "path", "TargetFile", "file_path"):
        val = args.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        print("{}")
        return

    tool_call = data.get("toolCall") or {}
    args = tool_call.get("args") or {}
    if isinstance(args, dict):
        raw_path = _extract_path(args)
        if raw_path and raw_path.endswith(".py"):
            ruff_bin = shutil.which("ruff")
            target = Path(raw_path)
            if ruff_bin and target.is_file():
                try:
                    proc = subprocess.run(
                        [ruff_bin, "check", "--quiet", str(target)],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if proc.returncode != 0:
                        msg = (proc.stdout or proc.stderr).strip()
                        if msg:
                            print(f"[post-edit-guard ruff] {msg}", file=sys.stderr)
                except Exception as exc:
                    print(f"[post-edit-guard] ruff check skipped: {exc}", file=sys.stderr)

    print("{}")


if __name__ == "__main__":
    main()
