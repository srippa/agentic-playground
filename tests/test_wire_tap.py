"""Offline deterministic unit tests for Stage 0 Part 0.2 (`tracer.py` and `wire_tap.py`)."""

from __future__ import annotations

import ast
import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest

from harness_lab.core.tracer import JsonlTraceWriter, WireTraceEvent, read_trace_events
from harness_lab.core.wire_tap import (
    REDACTED_VALUE,
    WireTapTransport,
    create_wire_tap_client,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


class _GatedSSEStream(httpx.AsyncByteStream):
    """Yields chunk 1 immediately, waits on `gate`, then yields chunk 2."""

    def __init__(self, gate: asyncio.Event) -> None:
        self._gate = gate

    async def __aiter__(self) -> AsyncIterator[bytes]:
        yield b'data: {"choices":[{"delta":{"content":"hello"}}]}\n\n'
        await self._gate.wait()
        yield b"data: [DONE]\n\n"


def test_non_streaming_json_capture_and_jsonl_roundtrip(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={"id": "cmpl-1", "choices": [{"message": {"content": "pong"}}]},
        )

    trace_file = tmp_path / "traces" / "non_stream.jsonl"

    async def scenario() -> None:
        client, tap = create_wire_tap_client(
            base_url="http://localhost:11434/v1",
            trace_path=trace_file,
            run_id="run-json",
            inner_transport=httpx.MockTransport(handler),
        )
        async with client:
            resp = await client.post(
                "/chat/completions",
                json={"model": "qwen3.8:27b", "messages": [{"role": "user", "content": "ping"}]},
            )
            assert resp.status_code == 200
            assert resp.json()["choices"][0]["message"]["content"] == "pong"
        assert len(tap.events) == 1

    asyncio.run(scenario())

    events = read_trace_events(trace_file)
    assert len(events) == 1
    ev = events[0]
    assert ev.seq == 1
    assert ev.run_id == "run-json"
    assert ev.method == "POST"
    assert ev.url == "http://localhost:11434/v1/chat/completions"
    assert ev.status_code == 200
    assert ev.request_body["model"] == "qwen3.8:27b"
    assert ev.response_body["id"] == "cmpl-1"
    assert ev.is_streaming is False
    assert ev.chunk_count >= 1
    assert ev.ttft_ms is not None and ev.ttft_ms >= 0.0
    assert ev.total_ms >= 0.0
    assert ev.error is None


def test_sse_streaming_does_not_buffer_and_records_ttft(tmp_path: Path) -> None:
    gate = asyncio.Event()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"Content-Type": "text/event-stream"},
            stream=_GatedSSEStream(gate),
        )

    trace_file = tmp_path / "sse.jsonl"
    received: list[bytes] = []

    async def scenario() -> None:
        client, _ = create_wire_tap_client(
            base_url="http://localhost:11434/v1",
            trace_path=trace_file,
            run_id="run-sse",
            inner_transport=httpx.MockTransport(handler),
        )
        async with client:
            async with client.stream(
                "POST",
                "/chat/completions",
                json={"model": "qwen3.8:27b", "stream": True},
            ) as resp:
                chunks = resp.aiter_bytes()
                first_chunk = await anext(chunks)
                received.append(first_chunk)
                # Proves chunk 1 arrived BEFORE chunk 2 was even unblocked:
                assert b"hello" in first_chunk
                gate.set()
                second_chunk = await anext(chunks)
                received.append(second_chunk)

    asyncio.run(scenario())

    assert len(received) == 2
    events = read_trace_events(trace_file)
    assert len(events) == 1
    ev = events[0]
    assert ev.is_streaming is True
    assert ev.chunk_count == 2
    assert ev.ttft_ms is not None
    assert ev.total_ms >= ev.ttft_ms
    assert "data: [DONE]" in ev.response_body


def test_early_stream_close_still_emits_single_trace_event(tmp_path: Path) -> None:
    gate = asyncio.Event()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"Content-Type": "text/event-stream"},
            stream=_GatedSSEStream(gate),
        )

    trace_file = tmp_path / "early_close.jsonl"

    async def scenario() -> None:
        client, tap = create_wire_tap_client(
            base_url="http://localhost:11434/v1",
            trace_path=trace_file,
            run_id="run-early",
            inner_transport=httpx.MockTransport(handler),
        )
        async with client:
            async with client.stream(
                "POST",
                "/chat/completions",
                json={"model": "qwen3.8:27b", "stream": True},
            ) as resp:
                async for chunk in resp.aiter_bytes():
                    assert b"hello" in chunk
                    break
        assert len(tap.events) == 1

    asyncio.run(scenario())

    events = read_trace_events(trace_file)
    assert len(events) == 1
    assert events[0].chunk_count == 1
    assert "hello" in events[0].response_body


def test_secret_headers_redacted_in_memory_and_on_disk(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={
                "Content-Type": "application/json",
                "Set-Cookie": "session=secret-cookie-val",
                "X-Custom-Secret": "custom-secret-val",
                "X-Request-Id": "req-42",
            },
            json={"ok": True},
        )

    trace_file = tmp_path / "redacted.jsonl"

    async def scenario() -> None:
        client, _ = create_wire_tap_client(
            base_url="https://api.example.com/v1",
            trace_path=trace_file,
            run_id="run-redact",
            inner_transport=httpx.MockTransport(handler),
            extra_redacted_headers=("X-Custom-Secret",),
        )
        async with client:
            await client.get(
                "/models",
                headers={
                    "Authorization": "Bearer sk-super-secret-999",
                    "X-API-Key": "top-secret-key",
                    "Cookie": "sid=abc-secret",
                    "X-Trace-Note": "safe-header",
                },
            )

    asyncio.run(scenario())

    raw_text = trace_file.read_text(encoding="utf-8")
    secrets = (
        "sk-super-secret-999",
        "top-secret-key",
        "abc-secret",
        "secret-cookie-val",
        "custom-secret-val",
    )
    for leaked in secrets:
        assert leaked not in raw_text

    ev = read_trace_events(trace_file)[0]
    assert ev.request_headers["authorization"] == REDACTED_VALUE
    assert ev.request_headers["x-api-key"] == REDACTED_VALUE
    assert ev.request_headers["cookie"] == REDACTED_VALUE
    assert ev.request_headers["x-trace-note"] == "safe-header"
    assert ev.response_headers["set-cookie"] == REDACTED_VALUE
    assert ev.response_headers["x-custom-secret"] == REDACTED_VALUE
    assert ev.response_headers["x-request-id"] == "req-42"


def test_transport_error_recorded_and_reraised(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused", request=request)

    trace_file = tmp_path / "err.jsonl"

    async def scenario() -> None:
        client, _ = create_wire_tap_client(
            base_url="http://localhost:11434/v1",
            trace_path=trace_file,
            run_id="run-err",
            inner_transport=httpx.MockTransport(handler),
        )
        async with client:
            with pytest.raises(httpx.ConnectError):
                await client.get("/models")

    asyncio.run(scenario())

    events = read_trace_events(trace_file)
    assert len(events) == 1
    assert events[0].status_code is None
    assert events[0].error is not None and "ConnectError" in events[0].error


def test_response_body_truncation_cap_preserves_caller_body(tmp_path: Path) -> None:
    payload = "x" * 200

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"Content-Type": "text/plain"}, text=payload)

    trace_file = tmp_path / "trunc.jsonl"

    async def scenario() -> None:
        client, _ = create_wire_tap_client(
            base_url="http://localhost:11434/v1",
            trace_path=trace_file,
            run_id="run-trunc",
            inner_transport=httpx.MockTransport(handler),
            max_capture_bytes=32,
        )
        async with client:
            resp = await client.get("/blob")
            assert resp.text == payload

    asyncio.run(scenario())

    ev = read_trace_events(trace_file)[0]
    assert ev.response_truncated is True
    assert isinstance(ev.response_body, str)
    assert len(ev.response_body) == 32


def test_on_event_hook_and_for_run_helper(tmp_path: Path) -> None:
    seen: list[WireTraceEvent] = []
    writer = JsonlTraceWriter.for_run("hook-run", traces_dir=tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    async def scenario() -> None:
        tap = WireTapTransport(
            inner=httpx.MockTransport(handler),
            writer=writer,
            run_id="hook-run",
            on_event=seen.append,
        )
        async with httpx.AsyncClient(transport=tap, base_url="http://localhost:11434") as client:
            await client.get("/api/tags")

    asyncio.run(scenario())

    assert len(seen) == 1
    assert writer.events_written == 1
    assert (tmp_path / "hook-run.jsonl").is_file()


def test_core_track_a_no_pydantic_ai_imports() -> None:
    for rel_path in (
        "src/harness_lab/core/__init__.py",
        "src/harness_lab/core/tracer.py",
        "src/harness_lab/core/wire_tap.py",
    ):
        tree = ast.parse((REPO_ROOT / rel_path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("pydantic_ai")
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("pydantic_ai")
