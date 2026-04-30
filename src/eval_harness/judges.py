"""Built-in judges.

A judge takes an ``Example`` and a ``Prediction`` and returns a ``Verdict``
with a numeric score in [0, 1] (or a raw value for cost / latency).

The runner aggregates verdicts into per-metric statistics. Adding a judge
means adding a kind here and wiring it in :func:`build_judge`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Optional

from .dataset import Example
from .schema import JudgeSpec
from .targets import Prediction


@dataclass
class Verdict:
    metric: str
    value: float
    passed: bool


JudgeFn = Callable[[Example, Prediction], Verdict]


def _exact_match(name: str) -> JudgeFn:
    def _judge(ex: Example, pred: Prediction) -> Verdict:
        ok = ex.expected.strip() == pred.output.strip()
        return Verdict(metric=name, value=1.0 if ok else 0.0, passed=ok)

    return _judge


def _contains(name: str) -> JudgeFn:
    def _judge(ex: Example, pred: Prediction) -> Verdict:
        ok = ex.expected.strip().lower() in pred.output.lower()
        return Verdict(metric=name, value=1.0 if ok else 0.0, passed=ok)

    return _judge


def _regex(name: str, pattern: str) -> JudgeFn:
    rx = re.compile(pattern)

    def _judge(_ex: Example, pred: Prediction) -> Verdict:
        ok = bool(rx.search(pred.output))
        return Verdict(metric=name, value=1.0 if ok else 0.0, passed=ok)

    return _judge


def _length(name: str, threshold: Optional[float]) -> JudgeFn:
    """Mean character length; threshold is treated as a *minimum*."""

    def _judge(_ex: Example, pred: Prediction) -> Verdict:
        n = float(len(pred.output))
        passed = (threshold is None) or (n >= threshold)
        return Verdict(metric=name, value=n, passed=passed)

    return _judge


def _latency(name: str, threshold: Optional[float]) -> JudgeFn:
    """Latency in ms; threshold is treated as a *maximum*."""

    def _judge(_ex: Example, pred: Prediction) -> Verdict:
        passed = (threshold is None) or (pred.latency_ms <= threshold)
        return Verdict(metric=name, value=pred.latency_ms, passed=passed)

    return _judge


def _cost(name: str, threshold: Optional[float]) -> JudgeFn:
    """Cost in USD per request; threshold is a *maximum*."""

    def _judge(_ex: Example, pred: Prediction) -> Verdict:
        passed = (threshold is None) or (pred.cost_usd <= threshold)
        return Verdict(metric=name, value=pred.cost_usd, passed=passed)

    return _judge


def build_judge(spec: JudgeSpec) -> JudgeFn:
    if spec.kind == "exact_match":
        return _exact_match(spec.name)
    if spec.kind == "contains":
        return _contains(spec.name)
    if spec.kind == "regex":
        if not spec.pattern:
            raise ValueError(f"Judge {spec.name} (regex) requires 'pattern'")
        return _regex(spec.name, spec.pattern)
    if spec.kind == "length":
        return _length(spec.name, spec.threshold)
    if spec.kind == "latency":
        return _latency(spec.name, spec.threshold)
    if spec.kind == "cost":
        return _cost(spec.name, spec.threshold)
    raise ValueError(f"Unknown judge kind: {spec.kind}")
