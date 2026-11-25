"""Stage 0 — Foundations: Local runtime doctor (`lab doctor`) (Track A framework-free)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from harness_lab.config import LabConfig
from harness_lab.core.tracer import JsonlTraceWriter, WireTraceEvent
from harness_lab.core.wire_tap import create_wire_tap_client

MIN_OLLAMA_VERSION: tuple[int, int, int] = (0, 33, 0)
BYTES_PER_GIB: float = float(1024**3)
ENV_HINT_KEYS: tuple[str, ...] = (
    "OLLAMA_MAX_LOADED_MODELS",
    "OLLAMA_CONTEXT_LENGTH",
    "OLLAMA_KV_CACHE_TYPE",
    "OLLAMA_FLASH_ATTENTION",
    "OLLAMA_NUM_PARALLEL",
)


class RunningModelInfo(BaseModel):
    """A model currently resident in Ollama unified memory (`/api/ps`)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    size_vram_gb: float = Field(ge=0.0)
    context_length: int | None = None
    expires_at: str | None = None


class ProfileCtxCheck(BaseModel):
    """Comparison of configured `models.toml` `num_ctx` vs. live runtime state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile: str
    model: str
    target_num_ctx: int
    installed: bool
    running_num_ctx: int | None = None
    show_num_ctx: int | None = None
    status: Literal["ok", "ctx_mismatch", "installed_not_loaded", "not_installed"]


class OllamaHealth(BaseModel):
    """Diagnostic health snapshot for the local Ollama daemon."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    native_base_url: str
    openai_base_url: str
    reachable: bool
    version: str | None = None
    version_ok: bool = False
    openai_compat_ok: bool = False
    installed_models: tuple[str, ...] = ()
    running_models: tuple[RunningModelInfo, ...] = ()
    active_vram_gb: float = 0.0
    headroom_gb: float
    within_vram_budget: bool
    profile_checks: tuple[ProfileCtxCheck, ...] = ()
    env_hints: dict[str, str | None] = Field(default_factory=dict)
    error: str | None = None


class OpenAICompatHealth(BaseModel):
    """Diagnostic health snapshot for LM Studio / OpenAI-compatible MLX server."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: str
    base_url: str
    reachable: bool
    models: tuple[str, ...] = ()
    bonsai_target_model: str
    bonsai_ready: bool = False
    error: str | None = None


class PingResult(BaseModel):
    """Result of an optional 1-token latency probe."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile: str
    model: str
    url: str
    ok: bool
    status_code: int | None = None
    ttft_ms: float | None = None
    total_ms: float | None = None
    error: str | None = None


class DoctorReport(BaseModel):
    """Aggregated `lab doctor` report."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ollama: OllamaHealth
    lmstudio: OpenAICompatHealth
    coresidency_summary: str
    coresidency_ok: bool
    ping: PingResult | None = None
    trace_path: Path | None = None
    warnings: tuple[str, ...] = ()

    @property
    def healthy(self) -> bool:
        return (
            self.ollama.reachable
            and self.ollama.within_vram_budget
            and (self.ping is None or self.ping.ok)
        )


def _parse_semver(version: str | None) -> tuple[int, int, int] | None:
    if not version:
        return None
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", version.strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _tag_matches(configured: str, candidate: str) -> bool:
    c_low = configured.strip().lower()
    cand_low = candidate.strip().lower()
    if c_low == cand_low:
        return True
    if ":" not in c_low and f"{c_low}:latest" == cand_low:
        return True
    if ":" not in cand_low and c_low == f"{cand_low}:latest":
        return True
    return False


def _extract_show_num_ctx(show_json: dict[str, Any]) -> int | None:
    parameters = show_json.get("parameters")
    if isinstance(parameters, str):
        match = re.search(r"^\s*num_ctx\s+(\d+)", parameters, re.MULTILINE)
        if match:
            return int(match.group(1))
    model_info = show_json.get("model_info")
    if isinstance(model_info, dict):
        for key, value in model_info.items():
            if key.endswith(".context_length") and isinstance(value, int):
                return value
    return None


def _collect_env_hints() -> dict[str, str | None]:
    import os

    return {key: os.environ.get(key) for key in ENV_HINT_KEYS}


async def _probe_ollama(
    config: LabConfig,
    *,
    writer: JsonlTraceWriter | None,
    run_id: str,
    captured_events: list[WireTraceEvent],
    timeout: float,
    transport: httpx.AsyncBaseTransport | None,
) -> tuple[OllamaHealth, list[str]]:
    ollama_profiles = [p for p in config.profiles.values() if p.provider == "ollama" and p.enabled]
    primary = ollama_profiles[0] if ollama_profiles else config.get_profile()
    native_url = (primary.native_base_url or "http://localhost:11434").rstrip("/")
    openai_url = primary.base_url.rstrip("/")
    ceiling = config.hardware.safe_wired_ceiling_gb
    env_hints = _collect_env_hints()
    warnings: list[str] = []

    if env_hints.get("OLLAMA_MAX_LOADED_MODELS") != "3":
        warnings.append(
            "Set OLLAMA_MAX_LOADED_MODELS=3 so workhorse + fast + embed stay hot concurrently."
        )
    if not env_hints.get("OLLAMA_CONTEXT_LENGTH"):
        warnings.append(
            "OLLAMA_CONTEXT_LENGTH is unset; Ollama /v1/chat/completions ignores request num_ctx."
        )

    client, _ = create_wire_tap_client(
        base_url=native_url,
        writer=writer,
        run_id=run_id,
        inner_transport=transport,
        on_event=captured_events.append,
        timeout=timeout,
    )

    async with client:
        try:
            ver_resp = await client.get("/api/version")
            ver_resp.raise_for_status()
            version = str(ver_resp.json().get("version", "")).strip() or None
        except Exception as exc:
            msg = f"Ollama unreachable at {native_url}: {type(exc).__name__}: {exc}"
            warnings.append(msg)
            return (
                OllamaHealth(
                    native_base_url=native_url,
                    openai_base_url=openai_url,
                    reachable=False,
                    headroom_gb=ceiling,
                    within_vram_budget=True,
                    env_hints=env_hints,
                    error=msg,
                ),
                warnings,
            )

        parsed_ver = _parse_semver(version)
        version_ok = parsed_ver is not None and parsed_ver >= MIN_OLLAMA_VERSION
        if not version_ok:
            warnings.append(
                f"Ollama version '{version or 'unknown'}' is below recommended v0.33.0+ floor."
            )

        installed_models: list[str] = []
        try:
            tags_resp = await client.get("/api/tags")
            tags_resp.raise_for_status()
            for item in tags_resp.json().get("models", []):
                name = item.get("name") or item.get("model")
                if isinstance(name, str) and name:
                    installed_models.append(name)
        except Exception as exc:
            warnings.append(f"Failed reading /api/tags: {exc}")

        running_models: list[RunningModelInfo] = []
        try:
            ps_resp = await client.get("/api/ps")
            ps_resp.raise_for_status()
            for item in ps_resp.json().get("models", []):
                name = str(item.get("name") or item.get("model") or "unknown")
                raw_vram = item.get("size_vram", item.get("size", 0)) or 0
                vram_gb = round(float(raw_vram) / BYTES_PER_GIB, 2)
                ctx = item.get("context_length")
                running_models.append(
                    RunningModelInfo(
                        name=name,
                        size_vram_gb=vram_gb,
                        context_length=int(ctx) if isinstance(ctx, int) else None,
                        expires_at=item.get("expires_at"),
                    )
                )
        except Exception as exc:
            warnings.append(f"Failed reading /api/ps: {exc}")

        openai_compat_ok = False
        try:
            v1_resp = await client.get(
                f"{openai_url}/models",
                headers={"Authorization": f"Bearer {primary.api_key_placeholder()}"},
            )
            openai_compat_ok = v1_resp.status_code == 200
        except Exception as exc:
            warnings.append(f"Ollama /v1/models check failed: {exc}")

        active_vram_gb = round(sum(m.size_vram_gb for m in running_models), 2)
        headroom_gb = round(ceiling - active_vram_gb, 2)
        within_vram = active_vram_gb <= ceiling
        if not within_vram:
            warnings.append(
                f"Loaded Ollama VRAM ({active_vram_gb:.1f} GB) exceeds safe wired ceiling "
                f"({ceiling:.1f} GB)."
            )

        profile_checks: list[ProfileCtxCheck] = []
        for prof in ollama_profiles:
            matched_tag = next(
                (tag for tag in installed_models if _tag_matches(prof.model, tag)),
                None,
            )
            running_match = next(
                (rm for rm in running_models if _tag_matches(prof.model, rm.name)),
                None,
            )
            show_ctx: int | None = None
            if matched_tag is not None:
                try:
                    show_resp = await client.post("/api/show", json={"model": matched_tag})
                    if show_resp.status_code == 200:
                        show_ctx = _extract_show_num_ctx(show_resp.json())
                except Exception:
                    show_ctx = None

            running_ctx = running_match.context_length if running_match else None
            if matched_tag is None and running_match is None:
                status: Literal["ok", "ctx_mismatch", "installed_not_loaded", "not_installed"] = (
                    "not_installed"
                )
            elif running_match is None:
                status = "installed_not_loaded"
            elif running_ctx is not None and running_ctx < prof.num_ctx:
                status = "ctx_mismatch"
                warnings.append(
                    f"Profile '{prof.name}' ({prof.model}) live context_length={running_ctx} "
                    f"is below target num_ctx={prof.num_ctx}."
                )
            else:
                status = "ok"

            profile_checks.append(
                ProfileCtxCheck(
                    profile=prof.name,
                    model=prof.model,
                    target_num_ctx=prof.num_ctx,
                    installed=matched_tag is not None,
                    running_num_ctx=running_ctx,
                    show_num_ctx=show_ctx,
                    status=status,
                )
            )

    return (
        OllamaHealth(
            native_base_url=native_url,
            openai_base_url=openai_url,
            reachable=True,
            version=version,
            version_ok=version_ok,
            openai_compat_ok=openai_compat_ok,
            installed_models=tuple(installed_models),
            running_models=tuple(running_models),
            active_vram_gb=active_vram_gb,
            headroom_gb=headroom_gb,
            within_vram_budget=within_vram,
            profile_checks=tuple(profile_checks),
            env_hints=env_hints,
        ),
        warnings,
    )


async def _probe_lmstudio(
    config: LabConfig,
    *,
    writer: JsonlTraceWriter | None,
    run_id: str,
    captured_events: list[WireTraceEvent],
    timeout: float,
    transport: httpx.AsyncBaseTransport | None,
) -> tuple[OpenAICompatHealth, list[str]]:
    bonsai_profile = config.profiles.get("bonsai-2.5")
    base_url = (
        bonsai_profile.base_url.rstrip("/")
        if bonsai_profile is not None
        else "http://localhost:1234/v1"
    )
    target_model = (
        bonsai_profile.model
        if bonsai_profile is not None
        else "prism-ml/Ternary-Bonsai-2.5-27B-mlx-2bit"
    )
    api_key = bonsai_profile.api_key_placeholder() if bonsai_profile else "lm-studio"

    client, _ = create_wire_tap_client(
        base_url=base_url,
        writer=writer,
        run_id=run_id,
        inner_transport=transport,
        on_event=captured_events.append,
        timeout=timeout,
    )

    async with client:
        try:
            resp = await client.get(
                "/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            models = tuple(
                str(item["id"])
                for item in data
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            )
        except Exception as exc:
            msg = f"LM Studio / MLX server not reachable at {base_url}: {type(exc).__name__}: {exc}"
            return (
                OpenAICompatHealth(
                    provider="lmstudio",
                    base_url=base_url,
                    reachable=False,
                    bonsai_target_model=target_model,
                    bonsai_ready=False,
                    error=msg,
                ),
                [msg],
            )

    bonsai_ready = any(
        mid.lower() == target_model.lower() or "bonsai" in mid.lower() for mid in models
    )
    return (
        OpenAICompatHealth(
            provider="lmstudio",
            base_url=base_url,
            reachable=True,
            models=models,
            bonsai_target_model=target_model,
            bonsai_ready=bonsai_ready,
        ),
        [],
    )


async def _run_ping(
    config: LabConfig,
    profile_name: str,
    *,
    writer: JsonlTraceWriter | None,
    run_id: str,
    captured_events: list[WireTraceEvent],
    timeout: float,
    ollama_transport: httpx.AsyncBaseTransport | None,
    lmstudio_transport: httpx.AsyncBaseTransport | None,
) -> PingResult:
    profile = config.get_profile(profile_name)
    transport = ollama_transport if profile.provider == "ollama" else lmstudio_transport

    if profile.api_style == "ollama_native":
        base = (profile.native_base_url or "http://localhost:11434").rstrip("/")
        path = "/api/embed" if profile.role == "embed" else "/api/chat"
        payload: dict[str, Any] = (
            {"model": profile.model, "input": "ping"}
            if path == "/api/embed"
            else {
                "model": profile.model,
                "messages": [{"role": "user", "content": "Reply OK"}],
                "stream": False,
                "options": {"num_predict": 1, "temperature": 0.0},
            }
        )
        headers: dict[str, str] = {}
    else:
        base = profile.base_url.rstrip("/")
        path = "/chat/completions"
        payload = {
            "model": profile.model,
            "messages": [{"role": "user", "content": "Reply OK"}],
            "max_tokens": 1,
            "temperature": 0.0,
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {profile.api_key_placeholder()}"}

    ping_events: list[WireTraceEvent] = []

    def _collect(ev: WireTraceEvent) -> None:
        ping_events.append(ev)
        captured_events.append(ev)

    client, _ = create_wire_tap_client(
        base_url=base,
        writer=writer,
        run_id=run_id,
        inner_transport=transport,
        on_event=_collect,
        timeout=max(timeout, 30.0),
    )

    full_url = f"{base}{path}"
    async with client:
        try:
            resp = await client.post(path, json=payload, headers=headers)
            ev = ping_events[-1] if ping_events else None
            ok = 200 <= resp.status_code < 300
            err = None if ok else f"HTTP {resp.status_code}: {resp.text[:200]}"
            return PingResult(
                profile=profile.name,
                model=profile.model,
                url=full_url,
                ok=ok,
                status_code=resp.status_code,
                ttft_ms=ev.ttft_ms if ev else None,
                total_ms=ev.total_ms if ev else None,
                error=err,
            )
        except Exception as exc:
            ev = ping_events[-1] if ping_events else None
            return PingResult(
                profile=profile.name,
                model=profile.model,
                url=full_url,
                ok=False,
                status_code=None,
                ttft_ms=ev.ttft_ms if ev else None,
                total_ms=ev.total_ms if ev else None,
                error=f"{type(exc).__name__}: {exc}",
            )


async def run_doctor(
    config: LabConfig,
    *,
    traces_dir: Path | str | None = Path("traces"),
    ping_profile: str | None = None,
    timeout: float = 3.0,
    ollama_transport: httpx.AsyncBaseTransport | None = None,
    lmstudio_transport: httpx.AsyncBaseTransport | None = None,
) -> tuple[DoctorReport, list[WireTraceEvent]]:
    """Run non-destructive runtime probes against local Ollama & LM Studio servers."""
    if ping_profile is not None:
        config.get_profile(ping_profile)

    run_id = f"doctor-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    writer = (
        JsonlTraceWriter.for_run(run_id, traces_dir=traces_dir)
        if traces_dir is not None
        else None
    )
    captured_events: list[WireTraceEvent] = []

    ollama_health, ollama_warnings = await _probe_ollama(
        config,
        writer=writer,
        run_id=run_id,
        captured_events=captured_events,
        timeout=timeout,
        transport=ollama_transport,
    )
    lmstudio_health, lm_warnings = await _probe_lmstudio(
        config,
        writer=writer,
        run_id=run_id,
        captured_events=captured_events,
        timeout=timeout,
        transport=lmstudio_transport,
    )

    ping_result: PingResult | None = None
    ping_warnings: list[str] = []
    if ping_profile is not None:
        ping_result = await _run_ping(
            config,
            ping_profile,
            writer=writer,
            run_id=run_id,
            captured_events=captured_events,
            timeout=timeout,
            ollama_transport=ollama_transport,
            lmstudio_transport=lmstudio_transport,
        )
        if not ping_result.ok:
            ping_warnings.append(
                f"Ping failed for '{ping_profile}': {ping_result.error}"
            )

    coresidency = config.check_coresidency()
    coresidency_summary = (
        f"{' + '.join(p.name for p in coresidency.profiles)}: "
        f"{coresidency.total_est_ram_gb:.1f} GB / "
        f"{coresidency.safe_wired_ceiling_gb:.1f} GB ceiling "
        f"({coresidency.model_count}/{coresidency.max_loaded_models} slots)"
    )

    all_warnings = tuple([*ollama_warnings, *lm_warnings, *ping_warnings])
    report = DoctorReport(
        ollama=ollama_health,
        lmstudio=lmstudio_health,
        coresidency_summary=coresidency_summary,
        coresidency_ok=coresidency.ok,
        ping=ping_result,
        trace_path=writer.path if writer is not None else None,
        warnings=all_warnings,
    )
    return report, captured_events


def render_doctor_report(
    report: DoctorReport,
    console: Console,
    *,
    xray: bool = False,
    events: Sequence[WireTraceEvent] = (),
) -> None:
    """Render `DoctorReport` and optional `--xray` wire events using Rich."""
    ol = report.ollama
    ol_status = (
        "[bold green]REACHABLE[/bold green]" if ol.reachable else "[bold red]OFFLINE[/bold red]"
    )
    ver_badge = (
        f"{ol.version} ([green]ok >= 0.33.0[/green])"
        if ol.version_ok
        else f"{ol.version or 'n/a'} ([yellow]check >= 0.33.0[/yellow])"
    )
    vram_badge = (
        f"[green]{ol.active_vram_gb:.1f} GB[/green]"
        if ol.within_vram_budget
        else f"[bold red]{ol.active_vram_gb:.1f} GB OVER CEILING[/bold red]"
    )
    ol_body = (
        f"Status: {ol_status} | Native: {ol.native_base_url} | OpenAI `/v1`: "
        f"{'[green]ok[/green]' if ol.openai_compat_ok else '[yellow]unavailable[/yellow]'}\n"
        f"Version: {ver_badge} | Installed tags: {len(ol.installed_models)} | "
        f"Loaded models: {len(ol.running_models)}\n"
        f"Active VRAM: {vram_badge} | Safe headroom: {ol.headroom_gb:+.1f} GB\n"
        f"Configured co-residency: {report.coresidency_summary}"
    )
    console.print(Panel(ol_body, title="Ollama & 64 GB Unified Memory", expand=False))

    if ol.running_models:
        ps_table = Table(title="Loaded Models (/api/ps)")
        ps_table.add_column("Model", style="bold cyan")
        ps_table.add_column("VRAM", justify="right")
        ps_table.add_column("Live num_ctx", justify="right")
        ps_table.add_column("Expires At")
        for rm in ol.running_models:
            ps_table.add_row(
                rm.name,
                f"{rm.size_vram_gb:.2f} GB",
                f"{rm.context_length:,}" if rm.context_length is not None else "n/a",
                rm.expires_at or "n/a",
            )
        console.print(ps_table)

    if ol.profile_checks:
        ctx_table = Table(title="Ollama Profile Readiness & num_ctx Check")
        ctx_table.add_column("Profile", style="bold cyan")
        ctx_table.add_column("Model")
        ctx_table.add_column("Target num_ctx", justify="right")
        ctx_table.add_column("Show / Live ctx", justify="right")
        ctx_table.add_column("Status")
        for chk in ol.profile_checks:
            live_str = (
                f"{chk.running_num_ctx:,}" if chk.running_num_ctx is not None else "-"
            )
            show_str = f"{chk.show_num_ctx:,}" if chk.show_num_ctx is not None else "-"
            status_map = {
                "ok": "[green]ok[/green]",
                "ctx_mismatch": "[bold red]ctx_mismatch[/bold red]",
                "installed_not_loaded": "[cyan]installed (idle)[/cyan]",
                "not_installed": "[dim]not pulled yet[/dim]",
            }
            ctx_table.add_row(
                chk.profile,
                chk.model,
                f"{chk.target_num_ctx:,}",
                f"{show_str} / {live_str}",
                status_map[chk.status],
            )
        console.print(ctx_table)

    lm = report.lmstudio
    lm_status = "[bold green]REACHABLE[/bold green]" if lm.reachable else "[yellow]OFFLINE[/yellow]"
    bonsai_badge = "[green]READY[/green]" if lm.bonsai_ready else "[dim]not detected[/dim]"
    lm_body = (
        f"Status: {lm_status} | Endpoint: {lm.base_url} | Listed models: {len(lm.models)}\n"
        f"Bonsai 2.5 ({lm.bonsai_target_model}): {bonsai_badge}"
    )
    console.print(Panel(lm_body, title="LM Studio / MLX & Bonsai 2.5", expand=False))

    if report.ping is not None:
        pg = report.ping
        pg_badge = "[bold green]PASS[/bold green]" if pg.ok else "[bold red]FAIL[/bold red]"
        pg_body = (
            f"Profile: {pg.profile} ({pg.model}) -> {pg_badge}\n"
            f"URL: {pg.url} | HTTP: {pg.status_code or 'n/a'} | "
            f"TTFT: {pg.ttft_ms if pg.ttft_ms is not None else 'n/a'} ms | "
            f"Total: {pg.total_ms if pg.total_ms is not None else 'n/a'} ms"
        )
        if pg.error:
            pg_body += f"\nError: {pg.error}"
        console.print(Panel(pg_body, title="1-Token Latency Ping", expand=False))

    if report.warnings:
        warn_lines = "\n".join(f"- {w}" for w in report.warnings)
        console.print(Panel(warn_lines, title="Advisories & Warnings", border_style="yellow"))

    if report.trace_path is not None:
        console.print(f"[dim]Redacted wire trace saved to:[/dim] {report.trace_path}")

    if xray and events:
        wire_table = Table(title="X-Ray Wire Events (Headers Redacted)")
        wire_table.add_column("Seq", justify="right")
        wire_table.add_column("Method")
        wire_table.add_column("URL")
        wire_table.add_column("Status", justify="right")
        wire_table.add_column("TTFT ms", justify="right")
        wire_table.add_column("Total ms", justify="right")
        wire_table.add_column("Error")
        for ev in events:
            wire_table.add_row(
                str(ev.seq),
                ev.method,
                ev.url,
                str(ev.status_code) if ev.status_code is not None else "-",
                f"{ev.ttft_ms:.1f}" if ev.ttft_ms is not None else "-",
                f"{ev.total_ms:.1f}",
                ev.error or "",
            )
        console.print(wire_table)
