"""Declarative eval-suite schema.

A suite is loaded from YAML and resolved into typed Pydantic models so the
runner, the diff engine, and the renderer all share one source of truth.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class DatasetSpec(BaseModel):
    """A pointer to a JSONL file of (input, expected) examples."""

    path: str
    limit: Optional[int] = Field(default=None, ge=1)


class JudgeSpec(BaseModel):
    """Declarative judge.

    Built-in kinds run with no API calls and require no network. The ``llm``
    kind is reserved for v0.2.
    """

    name: str
    kind: Literal["exact_match", "contains", "regex", "length", "latency", "cost"]
    threshold: Optional[float] = None
    pattern: Optional[str] = None
    field: Optional[str] = "output"

    @field_validator("kind")
    @classmethod
    def _validate_kind(cls, v: str) -> str:
        # Pydantic Literal already enforces this; explicit for clarity.
        return v


class GuardSpec(BaseModel):
    """Regression guard — the metric must not get worse than ``max_delta``.

    Direction matters:
      * ``higher_is_better=True``  -> regression is a *decrease*
      * ``higher_is_better=False`` -> regression is an *increase* (cost, latency)
    """

    metric: str
    higher_is_better: bool = True
    max_delta: float = 0.0  # absolute units of the metric


class TargetSpec(BaseModel):
    """The system under test. v0.1 supports ``mock`` (deterministic) and ``http``."""

    kind: Literal["mock", "http"]
    url: Optional[str] = None
    timeout_seconds: float = 30.0


class SuiteSpec(BaseModel):
    name: str
    target: TargetSpec
    dataset: DatasetSpec
    judges: List[JudgeSpec]
    guards: List[GuardSpec] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


def load_suite(path: str | Path) -> SuiteSpec:
    """Read and validate a YAML suite file."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    if not isinstance(raw, dict):
        raise ValueError(f"Suite file {path} must contain a YAML mapping at the top level.")
    return SuiteSpec(**raw)
