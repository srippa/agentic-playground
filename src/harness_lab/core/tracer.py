"""Structured JSONL wire-trace schema, writer, and reader (Track A framework-free)."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WireTraceEvent(BaseModel):
    """Single HTTP request/response (or transport error) captured at the wire layer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    seq: int = Field(ge=1)
    run_id: str = Field(min_length=1)
    timestamp_utc: str = Field(min_length=1)
    method: str = Field(min_length=1)
    url: str = Field(min_length=1)
    request_headers: dict[str, str] = Field(default_factory=dict)
    request_body: Any = None
    request_truncated: bool = False
    status_code: int | None = None
    response_headers: dict[str, str] = Field(default_factory=dict)
    response_body: Any = None
    response_truncated: bool = False
    is_streaming: bool = False
    chunk_count: int = Field(default=0, ge=0)
    ttft_ms: float | None = Field(default=None, ge=0.0)
    total_ms: float = Field(ge=0.0)
    error: str | None = None


class JsonlTraceWriter:
    """Thread-safe append-only JSONL writer for `WireTraceEvent` records."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self.events_written = 0

    @classmethod
    def for_run(
        cls,
        run_id: str,
        traces_dir: Path | str = Path("traces"),
    ) -> JsonlTraceWriter:
        """Create a writer targeting `<traces_dir>/<run_id>.jsonl`."""
        return cls(Path(traces_dir) / f"{run_id}.jsonl")

    def write(self, event: WireTraceEvent) -> None:
        """Append one validated event as a single JSON line."""
        line = event.model_dump_json() + "\n"
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line)
            self.events_written += 1


def read_trace_events(path: Path | str) -> list[WireTraceEvent]:
    """Load and validate all `WireTraceEvent` lines from a JSONL trace file."""
    trace_path = Path(path)
    if not trace_path.is_file():
        return []
    events: list[WireTraceEvent] = []
    with trace_path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue
            events.append(WireTraceEvent.model_validate_json(line))
    return events
