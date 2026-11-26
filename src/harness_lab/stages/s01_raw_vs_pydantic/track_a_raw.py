"""Stage 1 Part 1.1 — Track A raw `/v1/chat/completions` HTTP & SSE client (framework-free)."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

from harness_lab.config import ModelProfile
from harness_lab.core.tracer import JsonlTraceWriter, WireTraceEvent
from harness_lab.core.wire_tap import create_wire_tap_client

MessageRole = Literal["system", "user", "assistant", "tool"]


class ChatMessage(BaseModel):
    """Single message in OpenAI Chat Completions wire format."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: MessageRole
    content: str


class TokenUsage(BaseModel):
    """Token counts reported by `/v1/chat/completions`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    cached_tokens: int | None = Field(default=None, ge=0)
    cache_write_tokens: int | None = Field(default=None, ge=0)
    reasoning_tokens: int | None = Field(default=None, ge=0)


class SseChunkEvent(BaseModel):
    """One parsed Server-Sent Events `data:` frame from a streaming chat response."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    index: int = Field(ge=0)
    raw_data: str
    is_done: bool = False
    delta_content: str = ""
    delta_reasoning: str = ""
    finish_reason: str | None = None
    usage: TokenUsage | None = None
    raw_json: dict[str, Any] | None = None


class RawChatResult(BaseModel):
    """Complete output and wire telemetry from one Track A raw HTTP chat request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile: str
    model: str
    stream: bool
    request_payload: dict[str, Any]
    thinking: str = ""
    content: str = ""
    raw_content: str = ""
    finish_reason: str | None = None
    usage: TokenUsage | None = None
    sse_chunks: tuple[SseChunkEvent, ...] = ()
    raw_response_json: dict[str, Any] | None = None
    wire_events: tuple[WireTraceEvent, ...] = ()


def extract_thinking(
    text: str,
    *,
    open_tag: str = "<think>",
    close_tag: str = "</think>",
) -> tuple[str, str]:
    """Split inline `<think>...</think>` blocks from visible answer text."""
    if not open_tag or not close_tag:
        raise ValueError("open_tag and close_tag must be non-empty strings.")

    think_parts: list[str] = []
    clean_parts: list[str] = []
    pos = 0

    while pos < len(text):
        start = text.find(open_tag, pos)
        if start == -1:
            clean_parts.append(text[pos:])
            break

        clean_parts.append(text[pos:start])
        body_start = start + len(open_tag)
        end = text.find(close_tag, body_start)
        if end == -1:
            # Preserve truncated reasoning if max_tokens cut off before the closing tag.
            segment = text[body_start:].strip()
            if segment:
                think_parts.append(segment)
            break

        segment = text[body_start:end].strip()
        if segment:
            think_parts.append(segment)
        pos = end + len(close_tag)

    return "\n\n".join(think_parts), "".join(clean_parts).strip()


def build_chat_payload(
    profile: ModelProfile,
    messages: Sequence[ChatMessage],
    *,
    stream: bool = False,
    temperature: float | None = None,
    max_tokens: int | None = None,
    reasoning_effort: str | None = None,
    include_stream_usage: bool = True,
) -> dict[str, Any]:
    """Build the `/v1/chat/completions` JSON request payload without mutating `profile`."""
    if not messages:
        raise ValueError("messages must contain at least one ChatMessage.")

    payload: dict[str, Any] = {
        "model": profile.model,
        "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
        "temperature": profile.temperature if temperature is None else temperature,
        "stream": stream,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if reasoning_effort is not None:
        payload["reasoning_effort"] = reasoning_effort
    if stream and include_stream_usage:
        payload["stream_options"] = {"include_usage": True}
    return payload


def _first_int(*candidates: Any) -> int | None:
    for value in candidates:
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def _parse_usage(raw_usage: Any) -> TokenUsage | None:
    if not isinstance(raw_usage, dict):
        return None
    prompt_details = raw_usage.get("prompt_tokens_details")
    prompt_details_dict = prompt_details if isinstance(prompt_details, dict) else {}
    completion_details = raw_usage.get("completion_tokens_details")
    completion_details_dict = completion_details if isinstance(completion_details, dict) else {}

    return TokenUsage(
        prompt_tokens=_first_int(raw_usage.get("prompt_tokens")),
        completion_tokens=_first_int(raw_usage.get("completion_tokens")),
        total_tokens=_first_int(raw_usage.get("total_tokens")),
        cached_tokens=_first_int(
            prompt_details_dict.get("cached_tokens"),
            raw_usage.get("prompt_cache_hit_tokens"),
            raw_usage.get("cache_read_input_tokens"),
        ),
        cache_write_tokens=_first_int(
            prompt_details_dict.get("cache_write_tokens"),
            raw_usage.get("cache_creation_input_tokens"),
        ),
        reasoning_tokens=_first_int(completion_details_dict.get("reasoning_tokens")),
    )


def _extract_reasoning_field(obj: dict[str, Any]) -> str:
    for key in ("reasoning_content", "reasoning"):
        val = obj.get(key)
        if isinstance(val, str) and val:
            return val
    return ""


def parse_sse_frame(data_lines: Sequence[str], *, index: int) -> SseChunkEvent | None:
    """Parse buffered `data:` lines from a single SSE event into `SseChunkEvent`."""
    raw_data = "\n".join(data_lines).strip()
    if not raw_data:
        return None

    if raw_data == "[DONE]":
        return SseChunkEvent(index=index, raw_data=raw_data, is_done=True)

    try:
        parsed = json.loads(raw_data)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON in SSE frame #{index}: {raw_data[:120]}") from exc

    if not isinstance(parsed, dict):
        raise ValueError(f"Expected JSON object in SSE frame #{index}, got {type(parsed).__name__}")

    delta_content = ""
    delta_reasoning = ""
    finish_reason: str | None = None

    choices = parsed.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        choice = choices[0]
        raw_finish = choice.get("finish_reason")
        finish_reason = raw_finish if isinstance(raw_finish, str) else None
        delta = choice.get("delta")
        if isinstance(delta, dict):
            raw_content = delta.get("content")
            if isinstance(raw_content, str):
                delta_content = raw_content
            delta_reasoning = _extract_reasoning_field(delta)

    return SseChunkEvent(
        index=index,
        raw_data=raw_data,
        is_done=False,
        delta_content=delta_content,
        delta_reasoning=delta_reasoning,
        finish_reason=finish_reason,
        usage=_parse_usage(parsed.get("usage")),
        raw_json=parsed,
    )


class _SseLineAccumulator:
    """Incremental WHATWG-compliant SSE line parser for `data:` frames."""

    def __init__(self) -> None:
        self._data_lines: list[str] = []
        self._next_index = 0
        self.done = False

    def feed_line(self, raw_line: str) -> SseChunkEvent | None:
        """Consume one SSE line and emit an `SseChunkEvent` at event boundaries."""
        if self.done:
            return None

        line = raw_line.rstrip("\r\n")
        if line == "":
            return self.flush()

        if line.startswith(":"):
            return None

        if ":" in line:
            field, rest = line.split(":", 1)
            value = rest[1:] if rest.startswith(" ") else rest
        else:
            field, value = line, ""

        if field == "data":
            self._data_lines.append(value)
        return None

    def flush(self) -> SseChunkEvent | None:
        """Flush any buffered `data:` lines into a frame."""
        if self.done or not self._data_lines:
            self._data_lines.clear()
            return None

        buffered = self._data_lines
        self._data_lines = []
        event = parse_sse_frame(buffered, index=self._next_index)
        if event is not None:
            self._next_index += 1
            if event.is_done:
                self.done = True
        return event


def parse_sse_lines(lines: Iterable[str]) -> list[SseChunkEvent]:
    """Parse an iterable of raw SSE lines into ordered `SseChunkEvent` objects."""
    accumulator = _SseLineAccumulator()
    events: list[SseChunkEvent] = []
    for line in lines:
        event = accumulator.feed_line(line)
        if event is not None:
            events.append(event)
            if event.is_done:
                return events
    trailing = accumulator.flush()
    if trailing is not None:
        events.append(trailing)
    return events


def format_raw_json(data: Any) -> str:
    """Render a JSON-serializable wire payload as deterministic indented JSON."""
    return json.dumps(data, indent=2, ensure_ascii=False)


def _merge_thinking(
    *,
    native_reasoning: str,
    raw_content: str,
    open_think_tag: str,
    close_think_tag: str,
) -> tuple[str, str]:
    extracted_think, clean_content = extract_thinking(
        raw_content,
        open_tag=open_think_tag,
        close_tag=close_think_tag,
    )
    parts = [part for part in (native_reasoning.strip(), extracted_think) if part]
    return "\n\n".join(parts), clean_content


async def send_raw_chat(
    profile: ModelProfile,
    messages: Sequence[ChatMessage],
    *,
    stream: bool = False,
    temperature: float | None = None,
    max_tokens: int | None = None,
    reasoning_effort: str | None = None,
    include_stream_usage: bool = True,
    api_key: str | None = None,
    timeout: float = 60.0,
    trace_path: Path | str | None = None,
    writer: JsonlTraceWriter | None = None,
    run_id: str | None = None,
    inner_transport: httpx.AsyncBaseTransport | None = None,
    on_delta: Callable[[SseChunkEvent], None] | None = None,
    open_think_tag: str = "<think>",
    close_think_tag: str = "</think>",
) -> RawChatResult:
    """Send a raw OpenAI-compatible `/v1/chat/completions` request via `WireTapTransport`."""
    if profile.api_style != "openai_compat":
        raise ValueError(
            f"Profile '{profile.name}' uses api_style='{profile.api_style}'; "
            "Track A /v1/chat/completions requires 'openai_compat'."
        )

    resolved_key = api_key if api_key is not None else profile.api_key_placeholder()
    payload = build_chat_payload(
        profile,
        messages,
        stream=stream,
        temperature=temperature,
        max_tokens=max_tokens,
        reasoning_effort=reasoning_effort,
        include_stream_usage=include_stream_usage,
    )
    headers = {"Authorization": f"Bearer {resolved_key}"}

    client, tap = create_wire_tap_client(
        base_url=profile.base_url.rstrip("/"),
        trace_path=trace_path,
        writer=writer,
        run_id=run_id,
        inner_transport=inner_transport,
        timeout=timeout,
    )

    sse_chunks: list[SseChunkEvent] = []
    raw_response_json: dict[str, Any] | None = None
    raw_content = ""
    native_reasoning = ""
    finish_reason: str | None = None
    usage: TokenUsage | None = None

    async with client:
        if not stream:
            resp = await client.post("/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            raw_response_json = resp.json()
            if not isinstance(raw_response_json, dict):
                raise ValueError("Expected JSON object response from /chat/completions.")

            choices = raw_response_json.get("choices")
            if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                choice = choices[0]
                raw_finish = choice.get("finish_reason")
                finish_reason = raw_finish if isinstance(raw_finish, str) else None
                message = choice.get("message")
                if isinstance(message, dict):
                    msg_content = message.get("content")
                    if isinstance(msg_content, str):
                        raw_content = msg_content
                    native_reasoning = _extract_reasoning_field(message)
            usage = _parse_usage(raw_response_json.get("usage"))
        else:
            content_parts: list[str] = []
            reasoning_parts: list[str] = []
            accumulator = _SseLineAccumulator()

            async with client.stream(
                "POST",
                "/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status_code >= 400:
                    await resp.aread()
                    resp.raise_for_status()

                async for line in resp.aiter_lines():
                    event = accumulator.feed_line(line)
                    if event is None:
                        continue
                    sse_chunks.append(event)
                    if event.delta_content:
                        content_parts.append(event.delta_content)
                    if event.delta_reasoning:
                        reasoning_parts.append(event.delta_reasoning)
                    if event.finish_reason is not None:
                        finish_reason = event.finish_reason
                    if event.usage is not None:
                        usage = event.usage
                    if on_delta is not None:
                        on_delta(event)
                    if event.is_done:
                        break

                if not accumulator.done:
                    trailing = accumulator.flush()
                    if trailing is not None:
                        sse_chunks.append(trailing)
                        if trailing.delta_content:
                            content_parts.append(trailing.delta_content)
                        if trailing.delta_reasoning:
                            reasoning_parts.append(trailing.delta_reasoning)
                        if trailing.finish_reason is not None:
                            finish_reason = trailing.finish_reason
                        if trailing.usage is not None:
                            usage = trailing.usage
                        if on_delta is not None:
                            on_delta(trailing)

            raw_content = "".join(content_parts)
            native_reasoning = "".join(reasoning_parts)

    thinking, clean_content = _merge_thinking(
        native_reasoning=native_reasoning,
        raw_content=raw_content,
        open_think_tag=open_think_tag,
        close_think_tag=close_think_tag,
    )

    return RawChatResult(
        profile=profile.name,
        model=profile.model,
        stream=stream,
        request_payload=payload,
        thinking=thinking,
        content=clean_content,
        raw_content=raw_content,
        finish_reason=finish_reason,
        usage=usage,
        sse_chunks=tuple(sse_chunks),
        raw_response_json=raw_response_json,
        wire_events=tuple(tap.events),
    )
