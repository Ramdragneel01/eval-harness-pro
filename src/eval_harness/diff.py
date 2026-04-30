"""Diff engine: compare a head Result against a baseline Result.

Returns one ``MetricDelta`` per metric covering both runs. Guards (defined
in the suite) classify whether a delta is a *regression*, *improvement*, or
neutral. The PR-comment renderer consumes this directly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .runner import RunResult
from .schema import GuardSpec


@dataclass
class MetricDelta:
    metric: str
    head: float
    baseline: Optional[float]
    delta: Optional[float]
    higher_is_better: bool
    regression: bool
    improvement: bool


def diff_results(
    head: RunResult,
    baseline: Optional[RunResult],
    guards: List[GuardSpec],
) -> List[MetricDelta]:
    """Return per-metric deltas, applying guard direction + thresholds."""
    guard_map: Dict[str, GuardSpec] = {g.metric: g for g in guards}
    metrics = sorted(head.metrics.keys())
    deltas: List[MetricDelta] = []

    for name in metrics:
        h = head.metrics[name].mean
        b: Optional[float] = baseline.metrics[name].mean if baseline and name in baseline.metrics else None
        d: Optional[float] = (h - b) if b is not None else None

        guard = guard_map.get(name)
        higher_is_better = guard.higher_is_better if guard else True
        max_delta = guard.max_delta if guard else 0.0

        regression = False
        improvement = False
        if d is not None and guard is not None:
            if higher_is_better:
                # regression if head < baseline beyond tolerance
                if d < -max_delta:
                    regression = True
                elif d > 0:
                    improvement = True
            else:
                # higher is worse (cost, latency)
                if d > max_delta:
                    regression = True
                elif d < 0:
                    improvement = True

        deltas.append(
            MetricDelta(
                metric=name,
                head=h,
                baseline=b,
                delta=d,
                higher_is_better=higher_is_better,
                regression=regression,
                improvement=improvement,
            )
        )

    return deltas


def has_regression(deltas: List[MetricDelta]) -> bool:
    return any(d.regression for d in deltas)
