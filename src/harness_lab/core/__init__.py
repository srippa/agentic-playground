"""Core glass-box harness infrastructure (Track A framework-free)."""

from __future__ import annotations

from harness_lab.core.sandbox import (
    DEFAULT_SANDBOX_DIRNAME,
    SandboxViolationError,
    get_sandbox_root,
    resolve_sandbox_path,
    sandbox_db_path,
    sandbox_tool_outputs_dir,
)
from harness_lab.core.tracer import JsonlTraceWriter, WireTraceEvent, read_trace_events
from harness_lab.core.wire_tap import (
    DEFAULT_MAX_CAPTURE_BYTES,
    DEFAULT_REDACTED_HEADERS,
    REDACTED_VALUE,
    WireTapTransport,
    create_wire_tap_client,
    redact_headers,
)

__all__ = [
    "DEFAULT_MAX_CAPTURE_BYTES",
    "DEFAULT_REDACTED_HEADERS",
    "DEFAULT_SANDBOX_DIRNAME",
    "REDACTED_VALUE",
    "JsonlTraceWriter",
    "SandboxViolationError",
    "WireTapTransport",
    "WireTraceEvent",
    "create_wire_tap_client",
    "get_sandbox_root",
    "read_trace_events",
    "redact_headers",
    "resolve_sandbox_path",
    "sandbox_db_path",
    "sandbox_tool_outputs_dir",
]
