"""`lab` CLI entrypoint (Track A framework-free: stdlib argparse + rich)."""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from harness_lab import __version__
from harness_lab.config import ConfigError, LabConfig, load_config
from harness_lab.stages.s00_foundations.run import render_doctor_report, run_doctor


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level `lab` argument parser."""
    parser = argparse.ArgumentParser(
        prog="lab",
        description="Agentic Glass-Box Lab CLI (Track A raw & Track B PydanticAI v2)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    profiles_parser = subparsers.add_parser(
        "profiles",
        help="Show configured 64 GB Apple Silicon model profiles and co-residency budget",
    )
    profiles_parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional path to a models.toml file",
    )
    profiles_parser.add_argument(
        "--coresident",
        type=str,
        default=None,
        help="Comma-separated profile names to check against the 64 GB ceiling",
    )

    subparsers.add_parser("version", help="Print harness-lab and Python versions")
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Inspect local Ollama/LM Studio runtime health, num_ctx, and 64 GB headroom",
    )
    doctor_parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional path to a models.toml file",
    )
    doctor_parser.add_argument(
        "--ping",
        type=str,
        default=None,
        help="Optional local profile name for a 1-token latency ping",
    )
    doctor_parser.add_argument(
        "--traces-dir",
        type=Path,
        default=Path("traces"),
        help="Directory for redacted JSONL wire traces",
    )
    doctor_parser.add_argument(
        "--xray",
        action="store_true",
        help="Print wire-tap HTTP events captured during doctor probes",
    )
    doctor_parser.add_argument(
        "--strict",
        action="store_true",
        help="Return exit code 1 if Ollama is unreachable, over VRAM ceiling, or ping fails",
    )
    stage_parser = subparsers.add_parser(
        "stage",
        help="Run a curriculum stage demo (implemented across Stages 0-6)",
    )
    stage_parser.add_argument("stage_num", type=int, help="Stage number (0-6)")
    return parser


def _render_profiles(
    config: LabConfig,
    console: Console,
    coresident_arg: str | None,
) -> None:
    table = Table(title="Harness Lab Model Profiles (Apple Silicon 64 GB)")
    table.add_column("Profile", style="bold cyan")
    table.add_column("Provider")
    table.add_column("Model")
    table.add_column("API")
    table.add_column("num_ctx", justify="right")
    table.add_column("Est. RAM", justify="right")
    table.add_column("Status")

    for pname, profile in config.profiles.items():
        name_label = f"{pname} *" if pname == config.default_profile else pname
        if profile.is_cloud and not profile.enabled:
            status = "[yellow]cloud (disabled)[/yellow]"
        elif profile.is_cloud:
            status = "[yellow]cloud (opt-in)[/yellow]"
        elif profile.enabled:
            status = "[green]local ready[/green]"
        else:
            status = "[red]disabled[/red]"

        table.add_row(
            name_label,
            profile.provider,
            profile.model,
            profile.api_style,
            f"{profile.num_ctx:,}",
            f"{profile.est_ram_gb:.1f} GB",
            status,
        )

    console.print(table)

    names = (
        [item.strip() for item in coresident_arg.split(",") if item.strip()]
        if coresident_arg
        else None
    )
    report = config.check_coresidency(names)
    joined = " + ".join(p.name for p in report.profiles)
    verdict = "[bold green]OK[/bold green]" if report.ok else "[bold red]OVER BUDGET[/bold red]"
    summary = (
        f"Co-resident set: [bold]{joined}[/bold]\n"
        f"Estimated RAM: [bold]{report.total_est_ram_gb:.1f} GB[/bold] / "
        f"{report.safe_wired_ceiling_gb:.1f} GB safe ceiling "
        f"(of {config.hardware.unified_memory_gb:.0f} GB unified) "
        f"-> headroom: {report.headroom_gb:+.1f} GB\n"
        f"Loaded slots: {report.model_count} / {report.max_loaded_models} max | Verdict: {verdict}"
    )
    console.print(Panel(summary, title="64 GB Co-Residency Check", expand=False))


def main(argv: Sequence[str] | None = None, *, console: Console | None = None) -> int:
    """CLI entrypoint returning a process exit code."""
    out = console or Console()
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "version":
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        out.print(f"harness-lab {__version__} (Python {py_ver})")
        return 0

    if args.command == "profiles":
        try:
            config = load_config(args.config)
            _render_profiles(config, out, args.coresident)
        except ConfigError as exc:
            out.print(f"[bold red]Config error:[/bold red] {exc}")
            return 2
        return 0

    if args.command == "doctor":
        try:
            config = load_config(args.config)
            report, events = asyncio.run(
                run_doctor(
                    config,
                    traces_dir=args.traces_dir,
                    ping_profile=args.ping,
                )
            )
        except ConfigError as exc:
            out.print(f"[bold red]Config error:[/bold red] {exc}")
            return 2
        render_doctor_report(report, out, xray=args.xray, events=events)
        if args.strict and not report.healthy:
            return 1
        return 0

    if args.command == "stage":
        out.print(
            f"[yellow]lab stage {args.stage_num}[/yellow] runners will be wired starting in "
            "Stage 0/1 (Gate 3)."
        )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
