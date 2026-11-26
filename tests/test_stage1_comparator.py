"""Offline deterministic unit tests for Stage 1 Part 1.3 (comparator & `lab stage 1`)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from rich.console import Console

from harness_lab.cli import main
from harness_lab.config import find_repo_root, load_config
from harness_lab.core.tracer import read_trace_events
from harness_lab.stages.s01_raw_vs_pydantic.run import (
    diff_wire_payloads,
    render_stage1_report,
    run_stage1,
)

REPO_ROOT = find_repo_root(Path(__file__).resolve())


@pytest.fixture(autouse=True)
def _suppress_pydantic_ai_banner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYDANTIC_AI_NO_BANNER", "1")


def test_diff_wire_payloads_detects_shared_only_and_value_diffs() -> None:
    a = {
        "model": "qwen3.8:27b",
        "messages": [{"role": "user", "content": "hi"}],
        "stream": True,
        "stream_options": {"include_usage": True},
        "temperature": 0.1,
    }
    b = {
        "model": "qwen3.8:27b",
        "messages": [{"role": "user", "content": "hi"}],
        "stream": True,
        "temperature": 0.2,
        "reasoning_effort": "low",
    }
    diff = diff_wire_payloads(a, b)
    assert diff.messages_match is True
    assert diff.only_in_track_a == ("stream_options",)
    assert diff.only_in_track_b == ("reasoning_effort",)
    assert diff.shared_keys == ("messages", "model", "stream", "temperature")
    assert diff.different_values == {"temperature": (0.1, 0.2)}


@pytest.mark.parametrize("profile_name", ["workhorse", "fast", "bonsai-2.5"])
def test_run_stage1_offline_non_streaming_across_profiles(
    tmp_path: Path,
    profile_name: str,
) -> None:
    cfg = load_config(REPO_ROOT / "models.toml")
    report = asyncio.run(
        run_stage1(
            cfg,
            profile_name=profile_name,
            stream=False,
            offline=True,
            traces_dir=tmp_path,
        )
    )

    assert report.profile == profile_name
    assert report.stream is False
    assert report.offline is True
    assert "4291" not in report.track_a_turn2_stateless.content
    assert "4291" not in report.track_b_turn2_stateless.output
    assert "4291" in report.track_a_turn2_stateful.content
    assert "4291" in report.track_b_turn2_stateful.output

    assert report.track_a_turn1.usage is not None
    assert report.track_a_turn2_stateful.usage is not None
    assert (
        report.track_a_turn2_stateful.usage.prompt_tokens
        > report.track_a_turn1.usage.prompt_tokens
    )
    assert (
        report.track_b_turn2_stateful.usage.input_tokens
        > report.track_b_turn1.usage.input_tokens
    )
    assert report.turn1_wire_diff.messages_match is True
    # Track A omits prior thinking from Turn 2 history; Track B re-sends ThinkingPart by default.
    assert report.turn2_stateful_wire_diff.messages_match is False
    track_a_asst = report.turn2_stateful_wire_diff.track_a_body["messages"][2]
    track_b_asst = report.turn2_stateful_wire_diff.track_b_body["messages"][2]
    assert track_a_asst == {"role": "assistant", "content": "Code noted."}
    assert "<think>" in track_b_asst["content"] and "Code noted." in track_b_asst["content"]

    assert report.trace_path is not None and report.trace_path.is_file()
    events = read_trace_events(report.trace_path)
    assert len(events) == 6


def test_run_stage1_offline_streaming_sse_and_xray_render(tmp_path: Path) -> None:
    cfg = load_config(REPO_ROOT / "models.toml")
    report = asyncio.run(
        run_stage1(
            cfg,
            profile_name="fast",
            stream=True,
            offline=True,
            temperature=0.7,
            reasoning_effort="low",
            traces_dir=tmp_path,
        )
    )

    assert report.stream is True
    assert "4291" in report.track_a_turn2_stateful.content
    assert "4291" in report.track_b_turn2_stateful.output
    assert len(report.track_a_turn2_stateful.sse_chunks) == 5
    assert report.track_a_turn2_stateful.sse_chunks[-1].is_done is True
    assert report.turn1_wire_diff.messages_match is True
    assert report.turn2_stateful_wire_diff.messages_match is False
    track_b_asst = report.turn2_stateful_wire_diff.track_b_body["messages"][2]
    assert "reasoning" in track_b_asst and track_b_asst["content"] == "Code noted."

    console = Console(record=True, width=140)
    render_stage1_report(report, console, xray=True)
    rendered = console.export_text()
    assert "Statelessness Proof & Token Comparison" in rendered
    assert "IDENTICAL messages[]" in rendered
    assert "X-Ray: Track A Outgoing Wire JSON" in rendered
    assert "X-Ray: Track B Outgoing Wire JSON" in rendered
    assert "X-Ray: Track A Raw SSE Frames" in rendered
    assert "X-Ray: Track B ModelMessage Anatomy" in rendered
    assert "X-Ray: Captured Wire Events" in rendered


def test_cli_lab_stage_1_offline_xray_and_invalid_profile(tmp_path: Path) -> None:
    ok_console = Console(record=True, width=140)
    exit_code = main(
        [
            "stage",
            "1",
            "--offline",
            "--xray",
            "--profile",
            "fast",
            "--traces-dir",
            str(tmp_path),
        ],
        console=ok_console,
    )
    assert exit_code == 0
    out_text = ok_console.export_text()
    assert "qwen3.5:9b" in out_text
    assert "4291" in out_text
    assert "IDENTICAL messages[]" in out_text

    err_console = Console(record=True, width=120)
    bad_code = main(
        ["stage", "1", "--offline", "--profile", "embed"],
        console=err_console,
    )
    assert bad_code == 2
    assert "openai_compat" in err_console.export_text()
