"""Dataset loader.

Datasets are JSONL files where each line is an object with at least:
  {"input": "...", "expected": "..."}
Optional fields are passed through to judges via the ``Example.extra`` map.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional


@dataclass
class Example:
    input: str
    expected: str
    extra: Dict[str, Any] = field(default_factory=dict)


def iter_examples(path: str | Path, limit: Optional[int] = None) -> Iterator[Example]:
    """Yield examples from a JSONL file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset not found: {p}")
    with p.open("r", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            if limit is not None and i >= limit:
                break
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError(f"{p}:{i+1} is not a JSON object")
            inp = obj.pop("input", None)
            exp = obj.pop("expected", "")
            if inp is None:
                raise ValueError(f"{p}:{i+1} missing required 'input' field")
            yield Example(input=str(inp), expected=str(exp), extra=obj)


def load_examples(path: str | Path, limit: Optional[int] = None) -> List[Example]:
    return list(iter_examples(path, limit))
