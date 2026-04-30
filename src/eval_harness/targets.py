"""Targets — the system under test.

A target accepts an ``Example.input`` and returns a ``Prediction`` with the
generated text plus operational metadata (latency, token cost). v0.1 ships
two: a deterministic ``MockTarget`` for self-contained tests and an
``HttpTarget`` that POSTs to a JSON endpoint. New targets implement the
``Target`` protocol.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Protocol

import httpx

from .dataset import Example
from .schema import TargetSpec


@dataclass
class Prediction:
    output: str
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    raw: Dict[str, Any] = field(default_factory=dict)


class Target(Protocol):
    def predict(self, example: Example) -> Prediction: ...  # pragma: no cover


class MockTarget:
    """Echoes the expected answer (no failures) for tests and dry runs."""

    def __init__(self, latency_ms: float = 5.0, cost_usd: float = 0.0001) -> None:
        self.latency_ms = latency_ms
        self.cost_usd = cost_usd

    def predict(self, example: Example) -> Prediction:
        return Prediction(
            output=example.expected,
            latency_ms=self.latency_ms,
            cost_usd=self.cost_usd,
        )


class HttpTarget:
    """POST ``{"input": ...}`` to ``url``; expect ``{"output": "...", "cost_usd": ?}``."""

    def __init__(self, url: str, timeout_seconds: float = 30.0) -> None:
        self.url = url
        self.timeout = timeout_seconds

    def predict(self, example: Example) -> Prediction:
        start = time.perf_counter()
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(self.url, json={"input": example.input})
            r.raise_for_status()
            data = r.json()
        latency_ms = (time.perf_counter() - start) * 1000.0
        return Prediction(
            output=str(data.get("output", "")),
            latency_ms=latency_ms,
            cost_usd=float(data.get("cost_usd", 0.0)),
            raw=data,
        )


def build_target(spec: TargetSpec) -> Target:
    if spec.kind == "mock":
        return MockTarget()
    if spec.kind == "http":
        if not spec.url:
            raise ValueError("HttpTarget requires 'url'")
        return HttpTarget(url=spec.url, timeout_seconds=spec.timeout_seconds)
    raise ValueError(f"Unknown target kind: {spec.kind}")
