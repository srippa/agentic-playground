"""Framework-free `httpx.AsyncBaseTransport` wire tap with zero-buffering SSE tee."""

from __future__ import annotations

import json
import threading
import time
import uuid
from collections.abc import AsyncIterator, Callable, Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from harness_lab.core.tracer import JsonlTraceWriter, WireTraceEvent

DEFAULT_REDACTED_HEADERS: frozenset[str] = frozenset(
    {
        "authorization",
        "x-api-key",
        "api-key",
        "proxy-authorization",
        "cookie",
        "set-cookie",
    }
)
DEFAULT_MAX_CAPTURE_BYTES: int = 512_000
REDACTED_VALUE: str = "[REDACTED]"


def redact_headers(
    headers: httpx.Headers | Mapping[str, str],
    *,
    extra_redacted: Iterable[str] = (),
) -> dict[str, str]:
    """Return a dict copy of HTTP headers with sensitive values replaced by `[REDACTED]`."""
    sensitive = DEFAULT_REDACTED_HEADERS | {name.strip().lower() for name in extra_redacted}
    items = headers.multi_items() if isinstance(headers, httpx.Headers) else headers.items()
    redacted: dict[str, str] = {}
    for key, value in items:
        redacted[key] = REDACTED_VALUE if key.lower() in sensitive else value
    return redacted


def _decode_body(raw: bytes, *, content_type: str, truncated: bool) -> Any:
    """Decode captured HTTP bytes into parsed JSON (when safe) or UTF-8 text."""
    if not raw:
        return None
    text = raw.decode("utf-8", errors="replace")
    if truncated:
        return text

    lowered_ct = content_type.lower()
    stripped = text.lstrip()
    looks_like_json = (
        ("json" in lowered_ct and "ndjson" not in lowered_ct)
        or stripped.startswith("{")
        or stripped.startswith("[")
    )
    if looks_like_json:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return text


def _truncate_bytes(raw: bytes, max_bytes: int) -> tuple[bytes, bool]:
    if len(raw) <= max_bytes:
        return raw, False
    return raw[:max_bytes], True


class _TeeAsyncByteStream(httpx.AsyncByteStream):
    """Stream wrapper that yields chunks immediately while recording a bounded copy."""

    def __init__(
        self,
        inner_stream: httpx.AsyncByteStream,
        *,
        max_capture_bytes: int,
        start_perf: float,
        on_complete: Callable[[bytes, bool, int, float | None, float], None],
    ) -> None:
        self._inner_stream = inner_stream
        self._max_capture_bytes = max_capture_bytes
        self._start_perf = start_perf
        self._on_complete = on_complete
        self._buffer = bytearray()
        self._truncated = False
        self._chunk_count = 0
        self._first_chunk_perf: float | None = None
        self._finalized = False

    def _finalize(self) -> None:
        if self._finalized:
            return
        self._finalized = True
        total_ms = round((time.perf_counter() - self._start_perf) * 1000.0, 3)
        ttft_ms = (
            round((self._first_chunk_perf - self._start_perf) * 1000.0, 3)
            if self._first_chunk_perf is not None
            else None
        )
        self._on_complete(
            bytes(self._buffer),
            self._truncated,
            self._chunk_count,
            ttft_ms,
            total_ms,
        )

    async def __aiter__(self) -> AsyncIterator[bytes]:
        try:
            async for chunk in self._inner_stream:
                if chunk and self._first_chunk_perf is None:
                    self._first_chunk_perf = time.perf_counter()
                self._chunk_count += 1
                remaining = self._max_capture_bytes - len(self._buffer)
                if remaining > 0:
                    if len(chunk) <= remaining:
                        self._buffer.extend(chunk)
                    else:
                        self._buffer.extend(chunk[:remaining])
                        self._truncated = True
                elif chunk:
                    self._truncated = True
                yield chunk
        finally:
            self._finalize()

    async def aclose(self) -> None:
        try:
            await self._inner_stream.aclose()
        finally:
            self._finalize()


class WireTapTransport(httpx.AsyncBaseTransport):
    """`httpx.AsyncBaseTransport` wrapper capturing raw requests, streams, and timings."""

    def __init__(
        self,
        inner: httpx.AsyncBaseTransport | None = None,
        *,
        writer: JsonlTraceWriter | None = None,
        run_id: str | None = None,
        on_event: Callable[[WireTraceEvent], None] | None = None,
        max_capture_bytes: int = DEFAULT_MAX_CAPTURE_BYTES,
        extra_redacted_headers: Iterable[str] = (),
    ) -> None:
        if max_capture_bytes < 1:
            raise ValueError("max_capture_bytes must be >= 1")
        self._inner = inner or httpx.AsyncHTTPTransport()
        self._writer = writer
        self.run_id = run_id or uuid.uuid4().hex[:12]
        self._on_event = on_event
        self._max_capture_bytes = max_capture_bytes
        self._extra_redacted = tuple(extra_redacted_headers)
        self._lock = threading.Lock()
        self._seq = 0
        self.events: list[WireTraceEvent] = []

    def _emit_event(self, event_data: dict[str, Any]) -> WireTraceEvent:
        with self._lock:
            self._seq += 1
            seq = self._seq
        event = WireTraceEvent(seq=seq, **event_data)
        self.events.append(event)
        if self._writer is not None:
            self._writer.write(event)
        if self._on_event is not None:
            self._on_event(event)
        return event

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Forward an async HTTP request while capturing redacted wire telemetry."""
        try:
            raw_req = request.content
        except httpx.RequestNotRead:
            raw_req = await request.aread()

        req_slice, req_truncated = _truncate_bytes(raw_req, self._max_capture_bytes)
        req_headers = redact_headers(request.headers, extra_redacted=self._extra_redacted)
        req_ct = request.headers.get("content-type", "")
        decoded_req = _decode_body(req_slice, content_type=req_ct, truncated=req_truncated)

        timestamp_utc = datetime.now(UTC).isoformat()
        start_perf = time.perf_counter()

        try:
            response = await self._inner.handle_async_request(request)
        except Exception as exc:
            total_ms = round((time.perf_counter() - start_perf) * 1000.0, 3)
            self._emit_event(
                {
                    "run_id": self.run_id,
                    "timestamp_utc": timestamp_utc,
                    "method": request.method,
                    "url": str(request.url),
                    "request_headers": req_headers,
                    "request_body": decoded_req,
                    "request_truncated": req_truncated,
                    "status_code": None,
                    "response_headers": {},
                    "response_body": None,
                    "response_truncated": False,
                    "is_streaming": isinstance(decoded_req, dict)
                    and decoded_req.get("stream") is True,
                    "chunk_count": 0,
                    "ttft_ms": None,
                    "total_ms": total_ms,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            raise

        resp_headers = redact_headers(response.headers, extra_redacted=self._extra_redacted)
        resp_ct = response.headers.get("content-type", "")
        is_streaming = (
            "text/event-stream" in resp_ct.lower()
            or "ndjson" in resp_ct.lower()
            or (isinstance(decoded_req, dict) and decoded_req.get("stream") is True)
        )

        def _on_stream_complete(
            captured_resp: bytes,
            resp_truncated: bool,
            chunk_count: int,
            ttft_ms: float | None,
            total_ms: float,
        ) -> None:
            decoded_resp = _decode_body(
                captured_resp,
                content_type=resp_ct,
                truncated=resp_truncated,
            )
            self._emit_event(
                {
                    "run_id": self.run_id,
                    "timestamp_utc": timestamp_utc,
                    "method": request.method,
                    "url": str(request.url),
                    "request_headers": req_headers,
                    "request_body": decoded_req,
                    "request_truncated": req_truncated,
                    "status_code": response.status_code,
                    "response_headers": resp_headers,
                    "response_body": decoded_resp,
                    "response_truncated": resp_truncated,
                    "is_streaming": is_streaming,
                    "chunk_count": chunk_count,
                    "ttft_ms": ttft_ms,
                    "total_ms": total_ms,
                    "error": None,
                }
            )

        tee_stream = _TeeAsyncByteStream(
            response.stream,
            max_capture_bytes=self._max_capture_bytes,
            start_perf=start_perf,
            on_complete=_on_stream_complete,
        )
        return httpx.Response(
            status_code=response.status_code,
            headers=response.headers,
            stream=tee_stream,
            extensions=response.extensions,
        )

    async def aclose(self) -> None:
        await self._inner.aclose()


def create_wire_tap_client(
    *,
    base_url: str | None = None,
    trace_path: Path | str | None = None,
    writer: JsonlTraceWriter | None = None,
    run_id: str | None = None,
    inner_transport: httpx.AsyncBaseTransport | None = None,
    on_event: Callable[[WireTraceEvent], None] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout: float = 30.0,
    max_capture_bytes: int = DEFAULT_MAX_CAPTURE_BYTES,
    extra_redacted_headers: Iterable[str] = (),
) -> tuple[httpx.AsyncClient, WireTapTransport]:
    """Create an `(httpx.AsyncClient, WireTapTransport)` pair ready for Track A or Track B."""
    resolved_writer = writer
    if resolved_writer is None and trace_path is not None:
        resolved_writer = JsonlTraceWriter(trace_path)

    tap = WireTapTransport(
        inner=inner_transport,
        writer=resolved_writer,
        run_id=run_id,
        on_event=on_event,
        max_capture_bytes=max_capture_bytes,
        extra_redacted_headers=extra_redacted_headers,
    )
    client_kwargs: dict[str, Any] = {
        "transport": tap,
        "headers": dict(headers) if headers else None,
        "timeout": timeout,
    }
    if base_url is not None:
        client_kwargs["base_url"] = base_url
    client = httpx.AsyncClient(**client_kwargs)
    return client, tap
