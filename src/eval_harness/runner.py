"""Eval runner: executes a suite end-to-end and produces a Result.

The Result is a JSON-serializable structure containing per-metric aggregate
stats. The diff engine consumes two Results and yields a metric-by-metric
delta with regression/improvement classification.
"""
from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from .dataset import Example, load_examples
from .judges import Verdict, build_judge
from .schema import SuiteSpec
from .targets import build_target


@dataclass
class MetricStats:
    metric: str
    mean: float
    pass_rate: float
    n: int


@dataclass
class RunResult:
    suite: str
    n_examples: int
    metrics: Dict[str, MetricStats] = field(default_factory=dict)
    verdicts: List[Verdict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suite": self.suite,
            "n_examples": self.n_examples,
            "metrics": {k: asdict(v) for k, v in self.metrics.items()},
            "metadata": self.metadata,
        }


def run_suite(spec: SuiteSpec) -> RunResult:
    examples: List[Example] = load_examples(spec.dataset.path, limit=spec.dataset.limit)
    target = build_target(spec.target)
    judges = [build_judge(j) for j in spec.judges]
    judge_names = [j.name for j in spec.judges]

    all_verdicts: List[Verdict] = []
    by_metric: Dict[str, List[Verdict]] = {name: [] for name in judge_names}

    for ex in examples:
        pred = target.predict(ex)
        for judge in judges:
            v = judge(ex, pred)
            all_verdicts.append(v)
            by_metric[v.metric].append(v)

    metrics: Dict[str, MetricStats] = {}
    for name, verdicts in by_metric.items():
        if not verdicts:
            continue
        values = [v.value for v in verdicts]
        passes = [1.0 for v in verdicts if v.passed]
        metrics[name] = MetricStats(
            metric=name,
            mean=statistics.fmean(values),
            pass_rate=len(passes) / len(verdicts),
            n=len(verdicts),
        )

    return RunResult(
        suite=spec.name,
        n_examples=len(examples),
        metrics=metrics,
        verdicts=all_verdicts,
        metadata=dict(spec.metadata),
    )
