"""CLI: ``eval-harness run``, ``eval-harness diff``, ``eval-harness comment``.

Designed to be friendly to direct shell use *and* to GitHub Actions, where
each step typically calls one subcommand and persists artifacts between
steps via the filesystem.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from .diff import diff_results, has_regression
from .renderer import render_pr_comment
from .runner import RunResult, run_suite
from .schema import SuiteSpec, load_suite

console = Console()


def _result_to_json(result: RunResult) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True)


def _result_from_json(text: str) -> RunResult:
    data = json.loads(text)
    metrics = {}
    from .runner import MetricStats

    for name, m in data.get("metrics", {}).items():
        metrics[name] = MetricStats(**m)
    return RunResult(
        suite=data.get("suite", ""),
        n_examples=data.get("n_examples", 0),
        metrics=metrics,
        verdicts=[],
        metadata=data.get("metadata", {}),
    )


@click.group(help="Continuous evaluation CI for LLM applications.")
def main() -> None:  # pragma: no cover - entry point
    pass


@main.command("run", help="Run an eval suite and write a Result JSON.")
@click.option("--suite", "suite_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--out", "out_path", required=True, type=click.Path(dir_okay=False))
def cmd_run(suite_path: str, out_path: str) -> None:
    spec: SuiteSpec = load_suite(suite_path)
    result = run_suite(spec)
    Path(out_path).write_text(_result_to_json(result), encoding="utf-8")
    console.print(f"[green]✓[/green] Ran {spec.name}: {result.n_examples} examples → {out_path}")


@main.command("diff", help="Diff a head Result against a baseline Result.")
@click.option("--head", "head_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--baseline", "baseline_path", type=click.Path(dir_okay=False))
@click.option("--suite", "suite_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--out", "out_path", required=True, type=click.Path(dir_okay=False))
@click.option(
    "--fail-on-regression/--no-fail-on-regression",
    default=True,
    help="Exit non-zero if any guard reports a regression.",
)
def cmd_diff(
    head_path: str,
    baseline_path: Optional[str],
    suite_path: str,
    out_path: str,
    fail_on_regression: bool,
) -> None:
    spec: SuiteSpec = load_suite(suite_path)
    head = _result_from_json(Path(head_path).read_text(encoding="utf-8"))
    baseline = (
        _result_from_json(Path(baseline_path).read_text(encoding="utf-8"))
        if baseline_path and Path(baseline_path).exists()
        else None
    )
    deltas = diff_results(head, baseline, spec.guards)
    payload = {
        "suite": spec.name,
        "deltas": [asdict(d) for d in deltas],
        "regression": has_regression(deltas),
    }
    Path(out_path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    console.print(f"[green]✓[/green] Diff written → {out_path} (regression={payload['regression']})")
    if fail_on_regression and payload["regression"]:
        sys.exit(1)


@main.command("comment", help="Render a Markdown PR comment from a diff JSON.")
@click.option("--diff", "diff_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--out", "out_path", required=True, type=click.Path(dir_okay=False))
@click.option("--head-sha", default="", help="Optional commit SHA to include in the header.")
def cmd_comment(diff_path: str, out_path: str, head_sha: str) -> None:
    payload = json.loads(Path(diff_path).read_text(encoding="utf-8"))
    from .diff import MetricDelta

    deltas = [MetricDelta(**d) for d in payload.get("deltas", [])]
    body = render_pr_comment(deltas, payload.get("suite", ""), head_sha=head_sha)
    Path(out_path).write_text(body, encoding="utf-8")
    console.print(f"[green]✓[/green] PR comment written → {out_path}")


if __name__ == "__main__":  # pragma: no cover
    main()
