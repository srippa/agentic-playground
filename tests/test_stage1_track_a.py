"""Offline deterministic unit tests for Stage 1 Part 1.1 (Track A raw HTTP & SSE)."""

from __future__ import annotations

import ast
import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest

from harness_lab.config import ModelProfile
from harness_lab.core.tracer import read_trace_events
from harness_lab.core.wire_tap import REDACTED_VALUE
from harness_lab.stages.s01_raw_vs_pydantic.track_a_raw import (
    ChatMessage,
    SseChunkEvent,
    build_chat_payload,
    extract_thinking,
    format_raw_json,
    parse_sse_lines,
    send_raw_chat,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _local_profile(
    *,
    name: str = "workhorse",
    api_style: str = "openai_compat",
    temperature: float = 0.1,
) -> ModelProfile:
    return ModelProfile(
        name=name,
        role=name,
        provider="ollama",
        base_url="http://localhost:11434/v1",
        native_base_url="http://localhost:11434",
        model="qwen3.8:27b",
        api_style=api_style,  # type: ignore[arg-type]
        num_ctx=32768,
        keep_alive="30m",
        temperature=temperature,
        est_ram_gb=22.0,
        is_cloud=False,
        enabled=True,
    )


class _ChunkedByteStream(httpx.AsyncByteStream):
    """Emits explicit byte chunks so split `<think>` tags and SSE frames are tested."""

    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = chunks

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self._chunks:
            yield chunk


def test_extract_thinking_handles_common_and_edge_cases() -> None:
    assert extract_thinking("Plain answer.") == ("", "Plain answer.")

    thinking, clean = extract_thinking("<think>17 * 24 = 408</think>\nThe answer is 408.")
    assert thinking == "17 * 24 = 408"
    assert clean == "The answer is 408."

    multi_think, multi_clean = extract_thinking(
        "<think>Step 1</think>Hello <think>Step 2</think>world!"
    )
    assert multi_think == "Step 1\n\nStep 2"
    assert multi_clean == "Hello world!"

    truncated_think, truncated_clean = extract_thinking(
        "Intro <think>Halfway reasoning cut off by max_tokens"
    )
    assert truncated_think == "Halfway reasoning cut off by max_tokens"
    assert truncated_clean == "Intro"

    custom_think, custom_clean = extract_thinking(
        "[thought]internal[/thought]final",
        open_tag="[thought]",
        close_tag="[/thought]",
    )
    assert custom_think == "internal"
    assert custom_clean == "final"

    with pytest.raises(ValueError):
        extract_thinking("hi", open_tag="")


def test_build_chat_payload_options_and_validation() -> None:
    profile = _local_profile(temperature=0.1)
    msgs = [
        ChatMessage(role="system", content="Be concise."),
        ChatMessage(role="user", content="Ping"),
    ]

    non_stream = build_chat_payload(profile, msgs, stream=False)
    assert non_stream == {
        "model": "qwen3.8:27b",
        "messages": [
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Ping"},
        ],
        "temperature": 0.1,
        "stream": False,
    }

    stream_payload = build_chat_payload(
        profile,
        msgs,
        stream=True,
        temperature=0.7,
        max_tokens=128,
        reasoning_effort="low",
    )
    assert stream_payload["temperature"] == 0.7
    assert stream_payload["max_tokens"] == 128
    assert stream_payload["reasoning_effort"] == "low"
    assert stream_payload["stream"] is True
    assert stream_payload["stream_options"] == {"include_usage": True}

    no_usage_stream = build_chat_payload(
        profile,
        msgs,
        stream=True,
        include_stream_usage=False,
    )
    assert "stream_options" not in no_usage_stream

    with pytest.raises(ValueError):
        build_chat_payload(profile, [])


def test_parse_sse_lines_comments_multiline_reasoning_usage_and_done() -> None:
    lines = [
        ": keep-alive",
        "",
        'data: {"choices":[{"delta":{"reasoning_content":"check "}}]}',
        "",
        'data: {"choices":[{"delta":{"content":"42"}}]}',
        "",
        "data: {",
        'data: "choices":[{"delta":{"content":"!"},"finish_reason":"stop"}]',
        "data: }",
        "",
        'data: {"choices":[],"usage":{"prompt_tokens":10,"completion_tokens":4,"total_tokens":14}}',
        "",
        "data: [DONE]",
        "",
    ]

    events = parse_sse_lines(lines)
    assert len(events) == 5
    assert events[0].delta_reasoning == "check "
    assert events[1].delta_content == "42"
    assert events[2].delta_content == "!"
    assert events[2].finish_reason == "stop"
    assert events[3].usage is not None
    assert events[3].usage.total_tokens == 14
    assert events[4].is_done is True

    with pytest.raises(ValueError, match="Malformed JSON"):
        parse_sse_lines(["data: {not-json", ""])


def test_send_raw_chat_non_streaming_inline_think_and_redacted_trace(tmp_path: Path) -> None:
    seen_payloads: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_payloads.append(json.loads(request.content.decode("utf-8")))
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={
                "id": "chatcmpl-nonstream-1",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "<think>2 + 2 = 4</think>\n4",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 11, "completion_tokens": 8, "total_tokens": 19},
            },
        )

    trace_file = tmp_path / "s01_non_stream.jsonl"
    profile = _local_profile()
    result = asyncio.run(
        send_raw_chat(
            profile,
            [ChatMessage(role="user", content="What is 2+2?")],
            stream=False,
            trace_path=trace_file,
            run_id="s01-nonstream",
            inner_transport=httpx.MockTransport(handler),
        )
    )

    assert len(seen_payloads) == 1
    assert result.stream is False
    assert result.thinking == "2 + 2 = 4"
    assert result.content == "4"
    assert result.raw_content == "<think>2 + 2 = 4</think>\n4"
    assert result.finish_reason == "stop"
    assert result.usage is not None and result.usage.total_tokens == 19
    assert result.raw_response_json is not None
    assert json.loads(format_raw_json(result.raw_response_json))["id"] == "chatcmpl-nonstream-1"

    assert len(result.wire_events) == 1
    ev = result.wire_events[0]
    assert ev.is_streaming is False
    assert ev.request_headers["authorization"] == REDACTED_VALUE

    disk_events = read_trace_events(trace_file)
    assert len(disk_events) == 1
    assert "Bearer ollama" not in trace_file.read_text(encoding="utf-8")


def test_send_raw_chat_non_streaming_native_reasoning_fields() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "reasoning": "Native reasoning field.",
                            "content": "Final answer.",
                        },
                        "finish_reason": "stop",
                    }
                ]
            },
        )

    result = asyncio.run(
        send_raw_chat(
            _local_profile(),
            [ChatMessage(role="user", content="Hi")],
            inner_transport=httpx.MockTransport(handler),
        )
    )
    assert result.thinking == "Native reasoning field."
    assert result.content == "Final answer."


def test_send_raw_chat_streaming_sse_split_tags_and_live_deltas(tmp_path: Path) -> None:
    sse_frames = [
        b": stream open\n\n",
        b'data: {"choices":[{"delta":{"content":"<thi"}}]}\n\n',
        b'data: {"choices":[{"delta":{"content":"nk>step 1</th"}}]}\n\n',
        b'data: {"choices":[{"delta":{"content":"ink>Done."},"finish_reason":"stop"}]}\n\n',
        (
            b'data: {"choices":[],"usage":'
            b'{"prompt_tokens":14,"completion_tokens":7,"total_tokens":21}}\n\n'
        ),
        b"data: [DONE]\n\n",
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        assert body["stream"] is True
        assert body["stream_options"] == {"include_usage": True}
        return httpx.Response(
            200,
            headers={"Content-Type": "text/event-stream"},
            stream=_ChunkedByteStream(sse_frames),
        )

    live_events: list[SseChunkEvent] = []
    trace_file = tmp_path / "s01_stream.jsonl"
    result = asyncio.run(
        send_raw_chat(
            _local_profile(),
            [ChatMessage(role="user", content="Stream a test.")],
            stream=True,
            trace_path=trace_file,
            run_id="s01-stream",
            inner_transport=httpx.MockTransport(handler),
            on_delta=live_events.append,
        )
    )

    assert len(live_events) == 5
    assert result.sse_chunks == tuple(live_events)
    assert result.sse_chunks[-1].is_done is True
    assert result.raw_content == "<think>step 1</think>Done."
    assert result.thinking == "step 1"
    assert result.content == "Done."
    assert result.finish_reason == "stop"
    assert result.usage is not None
    assert result.usage.prompt_tokens == 14
    assert result.usage.completion_tokens == 7
    assert result.usage.total_tokens == 21
    assert result.raw_response_json is None

    assert len(result.wire_events) == 1
    wire = result.wire_events[0]
    assert wire.is_streaming is True
    assert wire.ttft_ms is not None and wire.ttft_ms >= 0.0
    assert len(read_trace_events(trace_file)) == 1


def test_multi_turn_statelessness_requires_resending_prior_messages() -> None:
    captured_turns: list[list[dict[str, str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        captured_turns.append(payload["messages"])
        turn_idx = len(captured_turns)
        reply = "Code noted." if turn_idx == 1 else "The secret code is 4291."
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": reply}}]},
        )

    profile = _local_profile()
    transport = httpx.MockTransport(handler)
    turn1_msgs = [ChatMessage(role="user", content="Remember the secret code is 4291.")]
    turn1 = asyncio.run(send_raw_chat(profile, turn1_msgs, inner_transport=transport))

    turn2_msgs = [
        *turn1_msgs,
        ChatMessage(role="assistant", content=turn1.content),
        ChatMessage(role="user", content="What is the secret code?"),
    ]
    turn2 = asyncio.run(send_raw_chat(profile, turn2_msgs, inner_transport=transport))

    assert len(captured_turns[0]) == 1
    assert len(captured_turns[1]) == 3
    assert turn2.request_payload["messages"][1] == {
        "role": "assistant",
        "content": "Code noted.",
    }
    assert turn2.content == "The secret code is 4291."


def test_http_error_records_wire_trace_and_rejects_ollama_native(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "model not pulled"})

    trace_file = tmp_path / "err.jsonl"
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(
            send_raw_chat(
                _local_profile(),
                [ChatMessage(role="user", content="Hi")],
                stream=True,
                trace_path=trace_file,
                inner_transport=httpx.MockTransport(handler),
            )
        )

    events = read_trace_events(trace_file)
    assert len(events) == 1
    assert events[0].status_code == 500

    embed_profile = _local_profile(name="embed", api_style="ollama_native")
    with pytest.raises(ValueError, match="openai_compat"):
        asyncio.run(
            send_raw_chat(
                embed_profile,
                [ChatMessage(role="user", content="Hi")],
            )
        )


def test_usage_parses_cache_and_reasoning_tokens_across_dialects() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "OK"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 1200,
                    "completion_tokens": 180,
                    "total_tokens": 1380,
                    "prompt_tokens_details": {"cached_tokens": 1024, "cache_write_tokens": 64},
                    "completion_tokens_details": {"reasoning_tokens": 140},
                },
            },
        )

    result = asyncio.run(
        send_raw_chat(
            _local_profile(),
            [ChatMessage(role="user", content="Cache test")],
            inner_transport=httpx.MockTransport(handler),
        )
    )
    assert result.usage is not None
    assert result.usage.prompt_tokens == 1200
    assert result.usage.cached_tokens == 1024
    assert result.usage.cache_write_tokens == 64
    assert result.usage.completion_tokens == 180
    assert result.usage.reasoning_tokens == 140

    sse_events = parse_sse_lines(
        [
            'data: {"choices":[{"delta":{"content":"Hi"},"finish_reason":"stop"}]}',
            "",
            (
                'data: {"choices":[],"usage":{"prompt_tokens":500,"completion_tokens":10,'
                '"total_tokens":510,"prompt_cache_hit_tokens":400,'
                '"cache_creation_input_tokens":50}}'
            ),
            "",
            "data: [DONE]",
            "",
        ]
    )
    usage = sse_events[1].usage
    assert usage is not None
    assert usage.cached_tokens == 400
    assert usage.cache_write_tokens == 50
    assert usage.reasoning_tokens is None

    minimal = parse_sse_lines(
        ['data: {"choices":[],"usage":{"prompt_tokens":5,"completion_tokens":2}}', ""]
    )
    assert minimal[0].usage is not None
    assert minimal[0].usage.cached_tokens is None
    assert minimal[0].usage.cache_write_tokens is None
    assert minimal[0].usage.reasoning_tokens is None


def test_track_a_raw_has_no_pydantic_ai_or_openai_sdk_imports() -> None:
    target = REPO_ROOT / "src" / "harness_lab" / "stages" / "s01_raw_vs_pydantic" / "track_a_raw.py"
    tree = ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith(("pydantic_ai", "openai"))
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith(("pydantic_ai", "openai"))
