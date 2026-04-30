"""Markdown renderer for PR comments.

Output is intentionally compact: a single header, one table, and a footer
that explains how to silence a noisy guard. GitHub Markdown renders this
inline in PRs without HTML hacks.
"""
from __future__ import annotations

from typing import List

from .diff import MetricDelta


def _fmt(value: float | None) -> str:
    if value is None:
        return "—"
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    if abs(value) >= 1:
        return f"{value:.3f}"
    return f"{value:.4f}"


def _badge(d: MetricDelta) -> str:
    if d.regression:
        return "🔴 regression"
    if d.improvement:
        return "🟢 improvement"
    if d.delta is None:
        return "⚪ new"
    return "⚪ neutral"


def render_pr_comment(deltas: List[MetricDelta], suite_name: str, head_sha: str = "") -> str:
    if not deltas:
        return f"### eval-harness-pro · `{suite_name}`\n\n_No metrics produced._"

    lines: List[str] = []
    lines.append(f"### eval-harness-pro · `{suite_name}`")
    if head_sha:
        lines.append(f"_Head: `{head_sha[:8]}`_")
    lines.append("")
    lines.append("| Metric | Head | Baseline | Δ | Status |")
    lines.append("| --- | ---: | ---: | ---: | --- |")
    for d in deltas:
        lines.append(
            f"| `{d.metric}` | {_fmt(d.head)} | {_fmt(d.baseline)} | {_fmt(d.delta)} | {_badge(d)} |"
        )
    if any(d.regression for d in deltas):
        lines.append("")
        lines.append("**Merge blocked** by `eval-harness-pro` due to one or more regressions.")
        lines.append("")
        lines.append("Adjust `guards[*].max_delta` in your suite YAML if the change is intentional.")
    else:
        lines.append("")
        lines.append("All guards passed.")
    return "\n".join(lines)
