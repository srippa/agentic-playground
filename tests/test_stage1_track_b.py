"""Offline deterministic unit tests for Stage 1 Part 1.2 (Track B PydanticAI adapter)."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from pydantic_ai import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.test import TestModel

from harness_lab.config import CloudProfileNotAllowedError, ModelProfile
from harness_lab.core.tracer import read_trace_events
from harness_lab.core.wire_tap import REDACTED_VALUE
from harness_lab.stages.s01_raw_vs_pydantic.track_b_pydantic import send_pydantic_chat


@pytest.fixture(autouse=True)
def _suppress_pydantic_ai_banner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYDANTIC_AI_NO_BANNER", "1")


def _local_profile(
    *,
    name: str = "workhorse",
    provider: str = "ollama",
    base_url: str = "http://localhost:11434/v1",
    model: str = "qwen3.8:27b",
    api_style: str = "openai_compat",
    is_cloud: bool = False,
) -> ModelProfile:
    return ModelProfile(
        name=name,
        role=name,
        provider=provider,  # type: ignore[arg-type]
        base_url=base_url,
        native_base_url="http://localhost:11434" if provider == "ollama" else None,
        model=model,
        api_style=api_style,  # type: ignore[arg-type]
        num_ctx=32768,
        keep_alive="30m",
        temperature=0.1,
        est_ram_gb=22.0,
        is_cloud=is_cloud,
        enabled=True,
    )


class _SseStream(httpx.AsyncByteStream):
    def __init__(self, frames: list[bytes]) -> None:
        self._frames = frames

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for frame in self._frames:
            yield frame


def test_non_streaming_inline_think_parts_and_redacted_wire_tap(tmp_path: Path) -> None:
    seen_payloads: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_payloads.append(json.loads(request.content.decode("utf-8")))
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={
                "id": "chatcmpl-trackb-1",
                "object": "chat.completion",
                "created": 1,
                "model": "qwen3.8:27b",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "<think>2 + 2 = 4</think>4",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 12, "completion_tokens": 6, "total_tokens": 18},
            },
        )

    trace_file = tmp_path / "trackb_nonstream.jsonl"
    result = asyncio.run(
        send_pydantic_chat(
            _local_profile(),
            "What is 2+2?",
            instructions="Be concise.",
            reasoning_effort="low",
            trace_path=trace_file,
            run_id="tb-nonstream",
            inner_transport=httpx.MockTransport(handler),
        )
    )

    assert len(seen_payloads) == 1
    assert seen_payloads[0]["reasoning_effort"] == "low"
    assert result.output == "4"
    assert result.thinking == "2 + 2 = 4"
    assert result.text == "4"
    assert result.finish_reason == "stop"
    assert result.usage.input_tokens == 12
    assert result.usage.output_tokens == 6
    assert result.usage.requests == 1

    assert [turn.kind for turn in result.message_tree] == ["request", "response"]
    req_turn, resp_turn = result.message_tree
    assert req_turn.instructions == "Be concise."
    assert [p.kind for p in req_turn.parts] == ["user-prompt"]
    assert [p.kind for p in resp_turn.parts] == ["thinking", "text"]
    assert resp_turn.parts[0].content == "2 + 2 = 4"
    assert resp_turn.parts[1].content == "4"

    assert len(result.wire_events) == 1
    assert result.wire_events[0].is_streaming is False
    assert result.wire_events[0].request_headers["authorization"] == REDACTED_VALUE
    assert len(read_trace_events(trace_file)) == 1
    assert "Bearer ollama" not in trace_file.read_text(encoding="utf-8")


def test_non_streaming_native_reasoning_and_cache_usage() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-native",
                "object": "chat.completion",
                "created": 1,
                "model": "qwen3.8:27b",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "reasoning": "Native reasoning block.",
                            "content": "Done.",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 500,
                    "completion_tokens": 40,
                    "total_tokens": 540,
                    "prompt_tokens_details": {"cached_tokens": 420},
                    "completion_tokens_details": {"reasoning_tokens": 30},
                },
            },
        )

    result = asyncio.run(
        send_pydantic_chat(
            _local_profile(),
            "Test native reasoning",
            inner_transport=httpx.MockTransport(handler),
        )
    )

    assert result.thinking == "Native reasoning block."
    assert result.text == "Done."
    assert result.output == "Done."
    assert result.usage.input_tokens == 500
    assert result.usage.output_tokens == 40
    assert result.usage.cache_read_tokens == 420
    assert result.usage.output_reasoning_tokens == 30


def test_streaming_sse_native_reasoning_live_deltas_and_wire_tap(tmp_path: Path) -> None:
    frames = [
        (
            b'data: {"id":"cmpl-s1","object":"chat.completion.chunk","created":1,'
            b'"model":"qwen3.8:27b","choices":[{"index":0,"delta":{"role":"assistant",'
            b'"reasoning":"step 1"}}]}\n\n'
        ),
        (
            b'data: {"id":"cmpl-s1","object":"chat.completion.chunk","created":1,'
            b'"model":"qwen3.8:27b","choices":[{"index":0,"delta":{"content":"Hel"}}]}\n\n'
        ),
        (
            b'data: {"id":"cmpl-s1","object":"chat.completion.chunk","created":1,'
            b'"model":"qwen3.8:27b","choices":[{"index":0,"delta":{"content":"lo!"},'
            b'"finish_reason":"stop"}]}\n\n'
        ),
        (
            b'data: {"id":"cmpl-s1","object":"chat.completion.chunk","created":1,'
            b'"model":"qwen3.8:27b","choices":[],"usage":{"prompt_tokens":100,'
            b'"completion_tokens":20,"total_tokens":120,'
            b'"prompt_tokens_details":{"cached_tokens":80},'
            b'"completion_tokens_details":{"reasoning_tokens":12}}}\n\n'
        ),
        b"data: [DONE]\n\n",
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        assert body["stream"] is True
        return httpx.Response(
            200,
            headers={"Content-Type": "text/event-stream"},
            stream=_SseStream(frames),
        )

    deltas: list[str] = []
    trace_file = tmp_path / "trackb_stream.jsonl"
    result = asyncio.run(
        send_pydantic_chat(
            _local_profile(),
            "Greet me",
            stream=True,
            trace_path=trace_file,
            run_id="tb-stream",
            inner_transport=httpx.MockTransport(handler),
            on_text_delta=deltas.append,
        )
    )

    assert deltas == ["Hel", "lo!"]
    assert result.stream is True
    assert result.thinking == "step 1"
    assert result.text == "Hello!"
    assert result.output == "Hello!"
    assert result.usage.input_tokens == 100
    assert result.usage.output_tokens == 20
    assert result.usage.cache_read_tokens == 80
    assert result.usage.output_reasoning_tokens == 12
    assert len(result.wire_events) == 1
    assert result.wire_events[0].is_streaming is True
    assert result.wire_events[0].ttft_ms is not None


def test_multi_turn_instructions_vs_system_prompt_anatomy() -> None:
    seen_histories: list[list[ModelMessage]] = []

    def responder(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen_histories.append(messages)
        return ModelResponse(parts=[TextPart(content=f"turn-{len(seen_histories)}")])

    fn_model = FunctionModel(responder)
    profile = _local_profile()

    inst_t1 = asyncio.run(
        send_pydantic_chat(
            profile,
            "Turn 1",
            instructions="Request-scoped rule.",
            model_override=fn_model,
        )
    )
    inst_t2 = asyncio.run(
        send_pydantic_chat(
            profile,
            "Turn 2",
            instructions="Updated rule.",
            message_history=inst_t1.all_messages,
            model_override=fn_model,
        )
    )
    assert [p.kind for p in inst_t2.message_tree[0].parts] == ["user-prompt"]
    assert inst_t2.message_tree[0].instructions == "Request-scoped rule."
    assert inst_t2.message_tree[2].instructions == "Updated rule."

    seen_histories.clear()
    sys_t1 = asyncio.run(
        send_pydantic_chat(
            profile,
            "Turn 1",
            system_prompt="Pinned system rule.",
            model_override=fn_model,
        )
    )
    sys_t2 = asyncio.run(
        send_pydantic_chat(
            profile,
            "Turn 2",
            system_prompt="Pinned system rule.",
            message_history=sys_t1.all_messages,
            model_override=fn_model,
        )
    )
    assert [p.kind for p in sys_t2.message_tree[0].parts] == ["system-prompt", "user-prompt"]
    assert [p.kind for p in sys_t2.message_tree[2].parts] == ["user-prompt"]
    assert len(sys_t2.all_messages) == 4


def test_offline_test_model_override_and_custom_thinking_tags() -> None:
    profile = _local_profile()
    test_res = asyncio.run(
        send_pydantic_chat(
            profile,
            "Offline check",
            model_override=TestModel(custom_output_text="offline ok"),
        )
    )
    assert test_res.output == "offline ok"
    assert test_res.wire_events == ()

    def custom_tag_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-custom",
                "object": "chat.completion",
                "created": 1,
                "model": "qwen3.8:27b",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "[thought]hidden[/thought]visible",
                        },
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    custom_res = asyncio.run(
        send_pydantic_chat(
            profile,
            "Custom tag",
            open_think_tag="[thought]",
            close_think_tag="[/thought]",
            inner_transport=httpx.MockTransport(custom_tag_handler),
        )
    )
    assert custom_res.thinking == "hidden"
    assert custom_res.text == "visible"


def test_lmstudio_uses_openai_provider_and_guards_invalid_profiles() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer lm-studio"
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-lms",
                "object": "chat.completion",
                "created": 1,
                "model": "prism-ml/Ternary-Bonsai-2.5-27B-mlx-2bit",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "Bonsai reply"},
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    bonsai = _local_profile(
        name="bonsai-2.5",
        provider="lmstudio",
        base_url="http://localhost:1234/v1",
        model="prism-ml/Ternary-Bonsai-2.5-27B-mlx-2bit",
    )
    res = asyncio.run(
        send_pydantic_chat(
            bonsai,
            "Hi Bonsai",
            inner_transport=httpx.MockTransport(handler),
        )
    )
    assert res.output == "Bonsai reply"

    embed = _local_profile(name="embed", api_style="ollama_native")
    with pytest.raises(ValueError, match="openai_compat"):
        asyncio.run(send_pydantic_chat(embed, "Hi"))

    cloud = _local_profile(
        name="oracle",
        provider="cloud",
        base_url="https://api.openai.com/v1",
        model="gpt-5",
        is_cloud=True,
    )
    with pytest.raises(CloudProfileNotAllowedError):
        asyncio.run(send_pydantic_chat(cloud, "Hi"))
