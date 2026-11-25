"""Offline deterministic unit tests for Stage 0 Part 0.3 (`lab doctor`)."""

from __future__ import annotations

import ast
import asyncio
import json
from pathlib import Path

import httpx
import pytest
from rich.console import Console

from harness_lab.cli import main
from harness_lab.config import CloudProfileNotAllowedError, find_repo_root, load_config
from harness_lab.core.tracer import read_trace_events
from harness_lab.stages.s00_foundations.run import render_doctor_report, run_doctor

REPO_ROOT = find_repo_root(Path(__file__).resolve())
GIB = 1024**3


def _make_ollama_mock(
    *,
    version: str = "0.40.18",
    tags: list[str] | None = None,
    running: list[dict[str, object]] | None = None,
    show_parameters: str = "num_ctx 32768",
    ping_capture: list[dict[str, object]] | None = None,
) -> httpx.MockTransport:
    tag_list = tags if tags is not None else ["qwen3.8:27b"]
    ps_list = running if running is not None else []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/api/version":
            return httpx.Response(200, json={"version": version})
        if path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": t} for t in tag_list]})
        if path == "/api/ps":
            return httpx.Response(200, json={"models": ps_list})
        if path == "/api/show":
            return httpx.Response(200, json={"parameters": show_parameters})
        if path == "/v1/models":
            return httpx.Response(
                200,
                json={"object": "list", "data": [{"id": t} for t in tag_list]},
            )
        if path == "/v1/chat/completions":
            body = json.loads(request.content.decode("utf-8"))
            if ping_capture is not None:
                ping_capture.append(body)
            return httpx.Response(
                200,
                json={
                    "id": "ping-1",
                    "choices": [{"message": {"role": "assistant", "content": "OK"}}],
                },
            )
        return httpx.Response(404, json={"error": f"Unhandled {path}"})

    return httpx.MockTransport(handler)


def _make_lmstudio_mock(model_ids: list[str] | None = None) -> httpx.MockTransport:
    ids = (
        model_ids
        if model_ids is not None
        else ["prism-ml/Ternary-Bonsai-2.5-27B-mlx-2bit"]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/models":
            return httpx.Response(
                200,
                json={"object": "list", "data": [{"id": mid} for mid in ids]},
            )
        return httpx.Response(404, json={"error": "not found"})

    return httpx.MockTransport(handler)


def _offline_mock() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused", request=request)

    return httpx.MockTransport(handler)


def test_doctor_healthy_ollama_and_lmstudio_bonsai_ready(tmp_path: Path) -> None:
    cfg = load_config(REPO_ROOT / "models.toml")
    ollama_mock = _make_ollama_mock(
        tags=["qwen3.8:27b", "qwen3.5:9b"],
        running=[
            {
                "name": "qwen3.8:27b",
                "size_vram": int(21.5 * GIB),
                "context_length": 32768,
                "expires_at": "2026-11-25T18:00:00Z",
            }
        ],
    )
    lm_mock = _make_lmstudio_mock()

    report, events = asyncio.run(
        run_doctor(
            cfg,
            traces_dir=tmp_path,
            ollama_transport=ollama_mock,
            lmstudio_transport=lm_mock,
        )
    )

    assert report.healthy is True
    assert report.ollama.reachable is True
    assert report.ollama.version == "0.40.18"
    assert report.ollama.version_ok is True
    assert report.ollama.openai_compat_ok is True
    assert report.ollama.active_vram_gb == 21.5
    assert report.ollama.headroom_gb == 24.5
    assert report.lmstudio.reachable is True
    assert report.lmstudio.bonsai_ready is True

    workhorse_chk = next(c for c in report.ollama.profile_checks if c.profile == "workhorse")
    assert workhorse_chk.status == "ok"
    assert workhorse_chk.show_num_ctx == 32768
    assert workhorse_chk.running_num_ctx == 32768

    assert report.trace_path is not None and report.trace_path.is_file()
    raw_trace = report.trace_path.read_text(encoding="utf-8")
    assert "Bearer ollama" not in raw_trace
    assert "Bearer lm-studio" not in raw_trace
    assert len(read_trace_events(report.trace_path)) == len(events)


def test_doctor_empty_ollama_and_offline_lmstudio(tmp_path: Path) -> None:
    cfg = load_config(REPO_ROOT / "models.toml")
    report, _ = asyncio.run(
        run_doctor(
            cfg,
            traces_dir=tmp_path,
            ollama_transport=_make_ollama_mock(tags=[], running=[]),
            lmstudio_transport=_offline_mock(),
        )
    )

    assert report.healthy is True
    assert report.ollama.reachable is True
    assert report.ollama.headroom_gb == 46.0
    assert report.lmstudio.reachable is False
    assert report.lmstudio.bonsai_ready is False
    assert all(chk.status == "not_installed" for chk in report.ollama.profile_checks)


def test_doctor_both_runtimes_offline(tmp_path: Path) -> None:
    cfg = load_config(REPO_ROOT / "models.toml")
    report, events = asyncio.run(
        run_doctor(
            cfg,
            traces_dir=tmp_path,
            ollama_transport=_offline_mock(),
            lmstudio_transport=_offline_mock(),
        )
    )

    assert report.healthy is False
    assert report.ollama.reachable is False
    assert report.lmstudio.reachable is False
    assert any("Ollama unreachable" in w for w in report.warnings)
    assert any(ev.error and "ConnectError" in ev.error for ev in events)


def test_doctor_detects_num_ctx_mismatch_and_vram_over_ceiling(tmp_path: Path) -> None:
    cfg = load_config(REPO_ROOT / "models.toml")
    ollama_mock = _make_ollama_mock(
        tags=["qwen3.8:27b"],
        running=[
            {
                "name": "qwen3.8:27b",
                "size_vram": int(48.0 * GIB),
                "context_length": 4096,
            }
        ],
    )
    report, _ = asyncio.run(
        run_doctor(
            cfg,
            traces_dir=tmp_path,
            ollama_transport=ollama_mock,
            lmstudio_transport=_offline_mock(),
        )
    )

    assert report.ollama.within_vram_budget is False
    assert report.healthy is False
    workhorse_chk = next(c for c in report.ollama.profile_checks if c.profile == "workhorse")
    assert workhorse_chk.status == "ctx_mismatch"
    assert any("context_length=4096" in w for w in report.warnings)
    assert any("exceeds safe wired ceiling" in w for w in report.warnings)


def test_doctor_optional_ping_and_cloud_guard(tmp_path: Path) -> None:
    cfg = load_config(REPO_ROOT / "models.toml")
    ping_payloads: list[dict[str, object]] = []
    ollama_mock = _make_ollama_mock(tags=["qwen3.8:27b"], ping_capture=ping_payloads)

    report, _ = asyncio.run(
        run_doctor(
            cfg,
            traces_dir=tmp_path,
            ping_profile="workhorse",
            ollama_transport=ollama_mock,
            lmstudio_transport=_offline_mock(),
        )
    )

    assert report.ping is not None
    assert report.ping.ok is True
    assert report.ping.status_code == 200
    assert report.ping.ttft_ms is not None and report.ping.ttft_ms >= 0.0
    assert report.ping.total_ms is not None and report.ping.total_ms >= 0.0
    assert ping_payloads[0]["max_tokens"] == 1
    assert "Bearer ollama" not in report.trace_path.read_text(encoding="utf-8")

    with pytest.raises(CloudProfileNotAllowedError):
        asyncio.run(
            run_doctor(
                cfg,
                traces_dir=tmp_path,
                ping_profile="oracle",
                ollama_transport=ollama_mock,
                lmstudio_transport=_offline_mock(),
            )
        )


def test_cli_doctor_default_strict_and_xray(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cfg = load_config(REPO_ROOT / "models.toml")
    offline_report, offline_events = asyncio.run(
        run_doctor(
            cfg,
            traces_dir=tmp_path,
            ollama_transport=_offline_mock(),
            lmstudio_transport=_offline_mock(),
        )
    )

    async def fake_run_doctor(*args: object, **kwargs: object) -> object:
        return offline_report, offline_events

    monkeypatch.setattr("harness_lab.cli.run_doctor", fake_run_doctor)

    rec = Console(record=True, width=120)
    assert main(["doctor", "--xray"], console=rec) == 0
    text = rec.export_text()
    assert "Ollama & 64 GB Unified Memory" in text
    assert "X-Ray Wire Events" in text

    strict_console = Console(record=True, width=120)
    assert main(["doctor", "--strict"], console=strict_console) == 1

    healthy_report, healthy_events = asyncio.run(
        run_doctor(
            cfg,
            traces_dir=tmp_path,
            ollama_transport=_make_ollama_mock(),
            lmstudio_transport=_make_lmstudio_mock(),
        )
    )
    render_console = Console(record=True, width=120)
    render_doctor_report(healthy_report, render_console, xray=True, events=healthy_events)
    assert "Bonsai 2.5" in render_console.export_text()


def test_s00_run_track_a_no_pydantic_ai_imports() -> None:
    path = REPO_ROOT / "src/harness_lab/stages/s00_foundations/run.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("pydantic_ai")
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("pydantic_ai")
