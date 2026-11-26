"""Stage 1 Part 1.2 — Track B PydanticAI single-turn adapter & message anatomy inspector."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ThinkingPart,
)
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import RunUsage

from harness_lab.config import ModelProfile
from harness_lab.core.tracer import JsonlTraceWriter, WireTraceEvent
from harness_lab.core.wire_tap import create_wire_tap_client

ReasoningEffort = Literal["low", "medium", "high"]


class MessagePartSummary(BaseModel):
    """Readable projection of one PydanticAI request or response part."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: str
    content: str
    provider_name: str | None = None


class MessageTurnSummary(BaseModel):
    """Readable projection of one `ModelRequest` or `ModelResponse` turn."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal["request", "response"]
    instructions: str | None = None
    parts: tuple[MessagePartSummary, ...] = ()
    model_name: str | None = None
    finish_reason: str | None = None


class PydanticUsageSummary(BaseModel):
    """Normalized token usage read from PydanticAI `RunUsage`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    cache_read_tokens: int = Field(default=0, ge=0)
    cache_write_tokens: int = Field(default=0, ge=0)
    output_reasoning_tokens: int = Field(default=0, ge=0)
    requests: int = Field(default=0, ge=0)


class PydanticChatResult(BaseModel):
    """Complete output, message tree, and wire telemetry from one Track B turn."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    profile: str
    model: str
    stream: bool
    output: str
    thinking: str = ""
    text: str = ""
    finish_reason: str | None = None
    usage: PydanticUsageSummary
    message_tree: tuple[MessageTurnSummary, ...] = ()
    all_messages: tuple[ModelMessage, ...] = ()
    wire_events: tuple[WireTraceEvent, ...] = ()


def build_pydantic_model(
    profile: ModelProfile,
    *,
    http_client: httpx.AsyncClient,
    api_key: str | None = None,
    open_think_tag: str = "<think>",
    close_think_tag: str = "</think>",
) -> OpenAIChatModel:
    """Build an `OpenAIChatModel` wired to `OllamaProvider` or `OpenAIProvider`."""
    if profile.api_style != "openai_compat":
        raise ValueError(
            f"Profile '{profile.name}' uses api_style='{profile.api_style}'; "
            "Track B OpenAIChatModel requires 'openai_compat'."
        )
    if not open_think_tag or not close_think_tag:
        raise ValueError("open_think_tag and close_think_tag must be non-empty strings.")

    resolved_key = api_key if api_key is not None else profile.api_key_placeholder()
    base_url = profile.base_url.rstrip("/")

    provider: OllamaProvider | OpenAIProvider
    if profile.provider == "ollama":
        provider = OllamaProvider(
            base_url=base_url,
            api_key=resolved_key,
            http_client=http_client,
        )
    else:
        provider = OpenAIProvider(
            base_url=base_url,
            api_key=resolved_key,
            http_client=http_client,
        )

    model_profile: OpenAIModelProfile | None = None
    if (open_think_tag, close_think_tag) != ("<think>", "</think>"):
        base_profile = provider.model_profile(profile.model)
        merged: dict[str, Any] = dict(base_profile) if base_profile is not None else {}
        merged["thinking_tags"] = (open_think_tag, close_think_tag)
        model_profile = OpenAIModelProfile(**merged)

    return OpenAIChatModel(
        profile.model,
        provider=provider,
        profile=model_profile,
    )


def _format_part_content(part: Any) -> str:
    content = getattr(part, "content", None)
    if isinstance(content, str):
        return content
    if content is None:
        return repr(part)
    return str(content)


def summarize_messages(messages: Sequence[ModelMessage]) -> tuple[MessageTurnSummary, ...]:
    """Project `ModelRequest` and `ModelResponse` history into readable summaries."""
    summaries: list[MessageTurnSummary] = []
    for msg in messages:
        part_summaries = tuple(
            MessagePartSummary(
                kind=part.part_kind,
                content=_format_part_content(part),
                provider_name=getattr(part, "provider_name", None),
            )
            for part in msg.parts
        )
        if isinstance(msg, ModelRequest):
            summaries.append(
                MessageTurnSummary(
                    kind="request",
                    instructions=msg.instructions,
                    parts=part_summaries,
                )
            )
        elif isinstance(msg, ModelResponse):
            summaries.append(
                MessageTurnSummary(
                    kind="response",
                    parts=part_summaries,
                    model_name=msg.model_name,
                    finish_reason=msg.finish_reason,
                )
            )
    return tuple(summaries)


def _extract_latest_thinking_and_text(
    messages: Sequence[ModelMessage],
) -> tuple[str, str, str | None]:
    for msg in reversed(messages):
        if isinstance(msg, ModelResponse):
            thinking_parts = [
                part.content.strip()
                for part in msg.parts
                if isinstance(part, ThinkingPart) and part.content.strip()
            ]
            text_parts = [part.content for part in msg.parts if isinstance(part, TextPart)]
            return (
                "\n\n".join(thinking_parts),
                "".join(text_parts),
                msg.finish_reason,
            )
    return "", "", None


def _summarize_usage(raw_usage: RunUsage) -> PydanticUsageSummary:
    return PydanticUsageSummary(
        input_tokens=raw_usage.input_tokens,
        output_tokens=raw_usage.output_tokens,
        cache_read_tokens=raw_usage.cache_read_tokens,
        cache_write_tokens=raw_usage.cache_write_tokens,
        output_reasoning_tokens=raw_usage.output_reasoning_tokens,
        requests=raw_usage.requests,
    )


def _build_model_settings(
    profile: ModelProfile,
    *,
    temperature: float | None,
    max_tokens: int | None,
    reasoning_effort: ReasoningEffort | None,
    include_openai_settings: bool,
) -> ModelSettings:
    resolved_temp = profile.temperature if temperature is None else temperature
    if include_openai_settings:
        settings: OpenAIChatModelSettings = {"temperature": resolved_temp}
        if max_tokens is not None:
            settings["max_tokens"] = max_tokens
        if reasoning_effort is not None:
            settings["openai_reasoning_effort"] = reasoning_effort
        return settings

    generic: ModelSettings = {"temperature": resolved_temp}
    if max_tokens is not None:
        generic["max_tokens"] = max_tokens
    return generic


async def _run_agent_turn(
    agent: Agent[None, str],
    prompt: str,
    *,
    history: list[ModelMessage] | None,
    stream: bool,
    on_text_delta: Callable[[str], None] | None,
) -> tuple[str, list[ModelMessage], RunUsage]:
    if not stream:
        result = await agent.run(prompt, message_history=history)
        return result.output, result.all_messages(), result.usage

    async with agent.run_stream(prompt, message_history=history) as streamed:
        async for delta in streamed.stream_text(delta=True, debounce_by=None):
            if on_text_delta is not None:
                on_text_delta(delta)
        output = await streamed.get_output()
        return output, streamed.all_messages(), streamed.usage


async def send_pydantic_chat(
    profile: ModelProfile,
    prompt: str,
    *,
    instructions: str | None = None,
    system_prompt: str | None = None,
    message_history: Sequence[ModelMessage] | None = None,
    stream: bool = False,
    temperature: float | None = None,
    max_tokens: int | None = None,
    reasoning_effort: ReasoningEffort | None = None,
    api_key: str | None = None,
    timeout: float = 60.0,
    trace_path: Path | str | None = None,
    writer: JsonlTraceWriter | None = None,
    run_id: str | None = None,
    inner_transport: httpx.AsyncBaseTransport | None = None,
    on_text_delta: Callable[[str], None] | None = None,
    model_override: Model | None = None,
    open_think_tag: str = "<think>",
    close_think_tag: str = "</think>",
) -> PydanticChatResult:
    """Run one Track B PydanticAI turn through `WireTapTransport` (or `model_override`)."""
    history = list(message_history) if message_history is not None else None
    settings = _build_model_settings(
        profile,
        temperature=temperature,
        max_tokens=max_tokens,
        reasoning_effort=reasoning_effort,
        include_openai_settings=model_override is None,
    )
    sys_prompts: Sequence[str] = (system_prompt,) if system_prompt is not None else ()

    if model_override is not None:
        agent = Agent(
            model_override,
            instructions=instructions,
            system_prompt=sys_prompts,
            model_settings=settings,
        )
        output, all_messages, raw_usage = await _run_agent_turn(
            agent,
            prompt,
            history=history,
            stream=stream,
            on_text_delta=on_text_delta,
        )
        wire_events: tuple[WireTraceEvent, ...] = ()
    else:
        client, tap = create_wire_tap_client(
            trace_path=trace_path,
            writer=writer,
            run_id=run_id,
            inner_transport=inner_transport,
            timeout=timeout,
        )
        async with client:
            model = build_pydantic_model(
                profile,
                http_client=client,
                api_key=api_key,
                open_think_tag=open_think_tag,
                close_think_tag=close_think_tag,
            )
            agent = Agent(
                model,
                instructions=instructions,
                system_prompt=sys_prompts,
                model_settings=settings,
            )
            output, all_messages, raw_usage = await _run_agent_turn(
                agent,
                prompt,
                history=history,
                stream=stream,
                on_text_delta=on_text_delta,
            )
        wire_events = tuple(tap.events)

    thinking, text, finish_reason = _extract_latest_thinking_and_text(all_messages)
    return PydanticChatResult(
        profile=profile.name,
        model=profile.model,
        stream=stream,
        output=output,
        thinking=thinking,
        text=text or output,
        finish_reason=finish_reason,
        usage=_summarize_usage(raw_usage),
        message_tree=summarize_messages(all_messages),
        all_messages=tuple(all_messages),
        wire_events=wire_events,
    )
