"""Stage 1 Part 1.3 — Side-by-side Track A vs. Track B `--xray` comparator & runner."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from harness_lab.config import LabConfig, ModelProfile
from harness_lab.core.tracer import JsonlTraceWriter, WireTraceEvent
from harness_lab.stages.s01_raw_vs_pydantic.track_a_raw import (
    ChatMessage,
    RawChatResult,
    format_raw_json,
    send_raw_chat,
)
from harness_lab.stages.s01_raw_vs_pydantic.track_b_pydantic import (
    PydanticChatResult,
    ReasoningEffort,
    send_pydantic_chat,
)

DEFAULT_INSTRUCTIONS: str = "You are a concise, accurate assistant."
DEFAULT_TURN1_PROMPT: str = "Remember the secret code is 4291."
DEFAULT_TURN2_PROMPT: str = "What is the secret code?"


class WirePayloadDiff(BaseModel):
    """Structural diff between Track A and Track B outgoing HTTP JSON bodies."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    track_a_body: dict[str, Any] = Field(default_factory=dict)
    track_b_body: dict[str, Any] = Field(default_factory=dict)
    shared_keys: tuple[str, ...] = ()
    only_in_track_a: tuple[str, ...] = ()
    only_in_track_b: tuple[str, ...] = ()
    different_values: dict[str, tuple[Any, Any]] = Field(default_factory=dict)
    messages_match: bool = False


class Stage1Report(BaseModel):
    """Full side-by-side comparison across Track A and Track B for a 2-turn probe."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile: str
    model: str
    provider: str
    base_url: str
    stream: bool
    offline: bool
    instructions: str
    turn1_prompt: str
    turn2_prompt: str
    track_a_turn1: RawChatResult
    track_a_turn2_stateless: RawChatResult
    track_a_turn2_stateful: RawChatResult
    track_b_turn1: PydanticChatResult
    track_b_turn2_stateless: PydanticChatResult
    track_b_turn2_stateful: PydanticChatResult
    turn1_wire_diff: WirePayloadDiff
    turn2_stateful_wire_diff: WirePayloadDiff
    trace_path: Path | None = None


def diff_wire_payloads(track_a_body: Any, track_b_body: Any) -> WirePayloadDiff:
    """Compare the actual outgoing HTTP JSON payloads captured by `WireTapTransport`."""
    body_a = track_a_body if isinstance(track_a_body, dict) else {}
    body_b = track_b_body if isinstance(track_b_body, dict) else {}

    keys_a = set(body_a)
    keys_b = set(body_b)
    shared = sorted(keys_a & keys_b)
    only_a = tuple(sorted(keys_a - keys_b))
    only_b = tuple(sorted(keys_b - keys_a))

    different: dict[str, tuple[Any, Any]] = {}
    for key in shared:
        if body_a[key] != body_b[key]:
            different[key] = (body_a[key], body_b[key])

    return WirePayloadDiff(
        track_a_body=body_a,
        track_b_body=body_b,
        shared_keys=tuple(shared),
        only_in_track_a=only_a,
        only_in_track_b=only_b,
        different_values=different,
        messages_match=body_a.get("messages") == body_b.get("messages"),
    )


class _MockSseByteStream(httpx.AsyncByteStream):
    """Emits OpenAI-compatible SSE chunks for offline Stage 1 comparator demos."""

    def __init__(self, frames: list[bytes]) -> None:
        self._frames = frames

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for frame in self._frames:
            yield frame


def build_offline_mock_transport(model: str) -> httpx.MockTransport:
    """Create a history-aware offline `MockTransport` demonstrating LLM statelessness."""

    def _reply_for_messages(messages: list[Any]) -> tuple[str, str]:
        prior_text = " ".join(
            str(msg.get("content", ""))
            for msg in messages[:-1]
            if isinstance(msg, dict)
        )
        last_user = ""
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "user":
                last_user = str(msg.get("content", ""))
                break

        lowered = last_user.lower()
        is_question = "?" in last_user or "what is" in lowered or "recall" in lowered
        if is_question and ("code" in lowered or "secret" in lowered):
            if "4291" in prior_text:
                return (
                    "Looking back at the supplied messages array, the secret code is 4291.",
                    "The secret code is 4291.",
                )
            return (
                "No secret code appears in the messages array on this request.",
                "I do not know — no secret code was provided in this conversation.",
            )
        if "4291" in last_user:
            return (
                "The user asked to remember 4291; acknowledging without storing server state.",
                "Code noted.",
            )
        return ("Processing single-turn prompt.", "Understood.")

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        messages = payload.get("messages")
        msg_list = messages if isinstance(messages, list) else []
        thinking, answer = _reply_for_messages(msg_list)

        prompt_tokens = max(12, len(json.dumps(msg_list)) // 4 + 6)
        reasoning_tokens = max(4, len(thinking.split()) + 2)
        answer_tokens = max(2, len(answer.split()) + 1)
        completion_tokens = reasoning_tokens + answer_tokens
        cached_tokens = max(0, prompt_tokens - 14) if len(msg_list) > 2 else 0
        usage_obj: dict[str, Any] = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "completion_tokens_details": {"reasoning_tokens": reasoning_tokens},
        }
        if cached_tokens > 0:
            usage_obj["prompt_tokens_details"] = {"cached_tokens": cached_tokens}

        if payload.get("stream") is True:
            mid = max(1, len(answer) // 2)
            part1, part2 = answer[:mid], answer[mid:]
            chunk_base = {
                "id": "chatcmpl-offline-sse",
                "object": "chat.completion.chunk",
                "created": 1,
                "model": payload.get("model", model),
            }
            frames = [
                b": offline mock stream\n\n",
                (
                    "data: "
                    + json.dumps(
                        {
                            **chunk_base,
                            "choices": [
                                {"index": 0, "delta": {"role": "assistant", "reasoning": thinking}}
                            ],
                        }
                    )
                    + "\n\n"
                ).encode("utf-8"),
                (
                    "data: "
                    + json.dumps(
                        {**chunk_base, "choices": [{"index": 0, "delta": {"content": part1}}]}
                    )
                    + "\n\n"
                ).encode("utf-8"),
                (
                    "data: "
                    + json.dumps(
                        {
                            **chunk_base,
                            "choices": [
                                {"index": 0, "delta": {"content": part2}, "finish_reason": "stop"}
                            ],
                        }
                    )
                    + "\n\n"
                ).encode("utf-8"),
                (
                    "data: "
                    + json.dumps({**chunk_base, "choices": [], "usage": usage_obj})
                    + "\n\n"
                ).encode("utf-8"),
                b"data: [DONE]\n\n",
            ]
            return httpx.Response(
                200,
                headers={"Content-Type": "text/event-stream"},
                stream=_MockSseByteStream(frames),
            )

        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={
                "id": "chatcmpl-offline",
                "object": "chat.completion",
                "created": 1,
                "model": payload.get("model", model),
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": f"<think>{thinking}</think>\n{answer}",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": usage_obj,
            },
        )

    return httpx.MockTransport(handler)


async def run_stage1(
    config: LabConfig,
    *,
    profile_name: str | None = None,
    stream: bool = False,
    offline: bool = False,
    temperature: float | None = None,
    reasoning_effort: ReasoningEffort | None = None,
    instructions: str = DEFAULT_INSTRUCTIONS,
    turn1_prompt: str = DEFAULT_TURN1_PROMPT,
    turn2_prompt: str = DEFAULT_TURN2_PROMPT,
    traces_dir: Path | str | None = Path("traces"),
    inner_transport: httpx.AsyncBaseTransport | None = None,
) -> Stage1Report:
    """Run Track A and Track B side-by-side through a 2-turn statelessness check."""
    profile: ModelProfile = config.get_profile(profile_name)
    if profile.api_style != "openai_compat":
        raise ValueError(
            f"Profile '{profile.name}' uses api_style='{profile.api_style}'; "
            "Stage 1 requires an 'openai_compat' chat profile (e.g. workhorse, fast, bonsai-2.5)."
        )

    transport = inner_transport
    if transport is None and offline:
        transport = build_offline_mock_transport(profile.model)

    run_id = f"s01-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    writer = (
        JsonlTraceWriter.for_run(run_id, traces_dir=traces_dir)
        if traces_dir is not None
        else None
    )

    base_msgs = [
        ChatMessage(role="system", content=instructions),
        ChatMessage(role="user", content=turn1_prompt),
    ]
    track_a_t1 = await send_raw_chat(
        profile,
        base_msgs,
        stream=stream,
        temperature=temperature,
        reasoning_effort=reasoning_effort,
        writer=writer,
        run_id=f"{run_id}-a1",
        inner_transport=transport,
    )
    track_a_t2_stateless = await send_raw_chat(
        profile,
        [
            ChatMessage(role="system", content=instructions),
            ChatMessage(role="user", content=turn2_prompt),
        ],
        stream=stream,
        temperature=temperature,
        reasoning_effort=reasoning_effort,
        writer=writer,
        run_id=f"{run_id}-a2-stateless",
        inner_transport=transport,
    )
    track_a_t2_stateful = await send_raw_chat(
        profile,
        [
            *base_msgs,
            ChatMessage(role="assistant", content=track_a_t1.content),
            ChatMessage(role="user", content=turn2_prompt),
        ],
        stream=stream,
        temperature=temperature,
        reasoning_effort=reasoning_effort,
        writer=writer,
        run_id=f"{run_id}-a2-stateful",
        inner_transport=transport,
    )

    track_b_t1 = await send_pydantic_chat(
        profile,
        turn1_prompt,
        instructions=instructions,
        stream=stream,
        temperature=temperature,
        reasoning_effort=reasoning_effort,
        writer=writer,
        run_id=f"{run_id}-b1",
        inner_transport=transport,
    )
    track_b_t2_stateless = await send_pydantic_chat(
        profile,
        turn2_prompt,
        instructions=instructions,
        stream=stream,
        temperature=temperature,
        reasoning_effort=reasoning_effort,
        writer=writer,
        run_id=f"{run_id}-b2-stateless",
        inner_transport=transport,
    )
    track_b_t2_stateful = await send_pydantic_chat(
        profile,
        turn2_prompt,
        instructions=instructions,
        message_history=track_b_t1.all_messages,
        stream=stream,
        temperature=temperature,
        reasoning_effort=reasoning_effort,
        writer=writer,
        run_id=f"{run_id}-b2-stateful",
        inner_transport=transport,
    )

    t1_diff = diff_wire_payloads(
        track_a_t1.wire_events[0].request_body if track_a_t1.wire_events else {},
        track_b_t1.wire_events[0].request_body if track_b_t1.wire_events else {},
    )
    t2_diff = diff_wire_payloads(
        track_a_t2_stateful.wire_events[0].request_body
        if track_a_t2_stateful.wire_events
        else {},
        track_b_t2_stateful.wire_events[0].request_body
        if track_b_t2_stateful.wire_events
        else {},
    )

    return Stage1Report(
        profile=profile.name,
        model=profile.model,
        provider=profile.provider,
        base_url=profile.base_url,
        stream=stream,
        offline=offline,
        instructions=instructions,
        turn1_prompt=turn1_prompt,
        turn2_prompt=turn2_prompt,
        track_a_turn1=track_a_t1,
        track_a_turn2_stateless=track_a_t2_stateless,
        track_a_turn2_stateful=track_a_t2_stateful,
        track_b_turn1=track_b_t1,
        track_b_turn2_stateless=track_b_t2_stateless,
        track_b_turn2_stateful=track_b_t2_stateful,
        turn1_wire_diff=t1_diff,
        turn2_stateful_wire_diff=t2_diff,
        trace_path=writer.path if writer is not None else None,
    )


def _fmt_tokens_raw(res: RawChatResult) -> str:
    if res.usage is None:
        return "n/a"
    cached = f" (cached {res.usage.cached_tokens})" if res.usage.cached_tokens else ""
    return f"{res.usage.prompt_tokens or 0} in{cached} / {res.usage.completion_tokens or 0} out"


def _fmt_tokens_pydantic(res: PydanticChatResult) -> str:
    u = res.usage
    cached = f" (cached {u.cache_read_tokens})" if u.cache_read_tokens else ""
    return f"{u.input_tokens} in{cached} / {u.output_tokens} out"


def _preview(text: str, limit: int = 72) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _render_wire_diff_panel(title: str, diff: WirePayloadDiff, console: Console) -> None:
    match_badge = (
        "[bold green]IDENTICAL messages[][/bold green]"
        if diff.messages_match
        else "[bold yellow]messages[] DIFFER[/bold yellow]"
    )
    diff_keys = ", ".join(sorted(diff.different_values)) or "none"
    body = (
        f"messages[] comparison: {match_badge}\n"
        f"Shared keys: {', '.join(diff.shared_keys) or 'none'}\n"
        f"Only in Track A: {', '.join(diff.only_in_track_a) or 'none'}\n"
        f"Only in Track B: {', '.join(diff.only_in_track_b) or 'none'}\n"
        f"Keys with different values: {diff_keys}"
    )
    console.print(Panel(body, title=title, expand=False))


def _all_wire_events(report: Stage1Report) -> list[tuple[str, WireTraceEvent]]:
    labeled: Sequence[tuple[str, Sequence[WireTraceEvent]]] = (
        ("Track A T1", report.track_a_turn1.wire_events),
        ("Track A T2 Stateless", report.track_a_turn2_stateless.wire_events),
        ("Track A T2 Stateful", report.track_a_turn2_stateful.wire_events),
        ("Track B T1", report.track_b_turn1.wire_events),
        ("Track B T2 Stateless", report.track_b_turn2_stateless.wire_events),
        ("Track B T2 Stateful", report.track_b_turn2_stateful.wire_events),
    )
    rows: list[tuple[str, WireTraceEvent]] = []
    for label, events in labeled:
        for ev in events:
            rows.append((label, ev))
    return rows


def render_stage1_report(
    report: Stage1Report,
    console: Console,
    *,
    xray: bool = False,
) -> None:
    """Render Stage 1 Track A vs. Track B comparison and optional `--xray` payloads."""
    mode = "SSE stream=True" if report.stream else "JSON stream=False"
    target = "offline mock" if report.offline else f"live ({report.base_url})"
    header = (
        f"Profile: [bold cyan]{report.profile}[/bold cyan] ({report.model}, {report.provider})\n"
        f"Mode: {mode} | Target: {target}\n"
        f"Turn 1: {report.turn1_prompt}\n"
        f"Turn 2: {report.turn2_prompt}"
    )
    console.print(Panel(header, title="Stage 1 — Raw HTTP vs. PydanticAI Model", expand=False))

    table = Table(title="Statelessness Proof & Token Comparison (Track A vs. Track B)")
    table.add_column("Turn")
    table.add_column("Track", style="bold")
    table.add_column("Answer")
    table.add_column("Thinking")
    table.add_column("Tokens (in / out)")

    rows = (
        ("1. Setup", "Track A (raw)", report.track_a_turn1.content, report.track_a_turn1.thinking,
         _fmt_tokens_raw(report.track_a_turn1)),
        ("1. Setup", "Track B (pydantic-ai)", report.track_b_turn1.output,
         report.track_b_turn1.thinking, _fmt_tokens_pydantic(report.track_b_turn1)),
        ("2a. Stateless (no history)", "Track A (raw)", report.track_a_turn2_stateless.content,
         report.track_a_turn2_stateless.thinking, _fmt_tokens_raw(report.track_a_turn2_stateless)),
        ("2a. Stateless (no history)", "Track B (pydantic-ai)",
         report.track_b_turn2_stateless.output, report.track_b_turn2_stateless.thinking,
         _fmt_tokens_pydantic(report.track_b_turn2_stateless)),
        ("2b. Stateful (+ history)", "Track A (raw)", report.track_a_turn2_stateful.content,
         report.track_a_turn2_stateful.thinking, _fmt_tokens_raw(report.track_a_turn2_stateful)),
        ("2b. Stateful (+ history)", "Track B (pydantic-ai)",
         report.track_b_turn2_stateful.output, report.track_b_turn2_stateful.thinking,
         _fmt_tokens_pydantic(report.track_b_turn2_stateful)),
    )
    for turn_label, track_label, ans, think, tok in rows:
        table.add_row(turn_label, track_label, _preview(ans), _preview(think or "-"), tok)
    console.print(table)

    _render_wire_diff_panel("Wire Diff — Turn 1 (Track A vs. Track B)", report.turn1_wire_diff,
                            console)
    _render_wire_diff_panel(
        "Wire Diff — Turn 2 Stateful (Track A vs. Track B)",
        report.turn2_stateful_wire_diff,
        console,
    )

    if report.trace_path is not None:
        console.print(f"[dim]Redacted wire trace saved to:[/dim] {report.trace_path}")

    if not xray:
        return

    console.print(
        Panel(
            Syntax(
                format_raw_json(report.turn2_stateful_wire_diff.track_a_body),
                "json",
                word_wrap=True,
            ),
            title="X-Ray: Track A Outgoing Wire JSON (Turn 2 Stateful)",
        )
    )
    console.print(
        Panel(
            Syntax(
                format_raw_json(report.turn2_stateful_wire_diff.track_b_body),
                "json",
                word_wrap=True,
            ),
            title="X-Ray: Track B Outgoing Wire JSON (Turn 2 Stateful)",
        )
    )

    if report.stream and report.track_a_turn2_stateful.sse_chunks:
        sse_table = Table(title="X-Ray: Track A Raw SSE Frames (Turn 2 Stateful)")
        sse_table.add_column("#", justify="right")
        sse_table.add_column("Done")
        sse_table.add_column("delta.reasoning")
        sse_table.add_column("delta.content")
        sse_table.add_column("finish_reason")
        for chunk in report.track_a_turn2_stateful.sse_chunks:
            sse_table.add_row(
                str(chunk.index),
                "yes" if chunk.is_done else "-",
                _preview(chunk.delta_reasoning or "-", 48),
                _preview(chunk.delta_content or "-", 48),
                chunk.finish_reason or "-",
            )
        console.print(sse_table)

    msg_table = Table(title="X-Ray: Track B ModelMessage Anatomy (Turn 2 Stateful)")
    msg_table.add_column("Step", justify="right")
    msg_table.add_column("Message Type")
    msg_table.add_column("Instructions")
    msg_table.add_column("Parts")
    for idx, turn in enumerate(report.track_b_turn2_stateful.message_tree, start=1):
        part_lines = "\n".join(
            f"{escape(f'[{p.kind}]')} {escape(_preview(p.content, 60))}" for p in turn.parts
        )
        msg_table.add_row(
            str(idx),
            f"Model{turn.kind.capitalize()}",
            escape(_preview(turn.instructions or "-", 40)),
            part_lines,
        )
    console.print(msg_table)

    wire_table = Table(title="X-Ray: Captured Wire Events (Headers Redacted)")
    wire_table.add_column("Call")
    wire_table.add_column("Seq", justify="right")
    wire_table.add_column("Status", justify="right")
    wire_table.add_column("Stream")
    wire_table.add_column("TTFT ms", justify="right")
    wire_table.add_column("Total ms", justify="right")
    for label, ev in _all_wire_events(report):
        wire_table.add_row(
            label,
            str(ev.seq),
            str(ev.status_code) if ev.status_code is not None else "-",
            "yes" if ev.is_streaming else "no",
            f"{ev.ttft_ms:.1f}" if ev.ttft_ms is not None else "-",
            f"{ev.total_ms:.1f}",
        )
    console.print(wire_table)
