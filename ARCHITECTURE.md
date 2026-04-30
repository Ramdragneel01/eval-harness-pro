# Architecture — eval-harness-pro

## Goal

Make LLM evals first-class CI citizens. Engineers should see metric deltas in the PR they are reviewing — not in a dashboard nobody opens — and a regression should block merge automatically.

## Component View

```
┌───────────────────────────────────────────────────────────────────┐
│                         eval-harness-pro                          │
│                                                                   │
│  suite.yaml ─► schema.SuiteSpec ─► runner.run_suite ─► RunResult  │
│                                       │                           │
│                                       ▼                           │
│   targets (mock|http) ─►  judges (exact|contains|regex|...)       │
│                                       │                           │
│                                       ▼                           │
│   baseline RunResult ─► diff.diff_results ─► [MetricDelta]        │
│                                       │                           │
│                                       ▼                           │
│                          renderer.render_pr_comment               │
│                                       │                           │
│                                       ▼                           │
│                   Markdown body posted by the GH Action           │
└───────────────────────────────────────────────────────────────────┘
```

## Module Map

| Module                     | Responsibility                                                  |
| -------------------------- | --------------------------------------------------------------- |
| `eval_harness.schema`      | Pydantic models for suites, datasets, judges, guards, targets   |
| `eval_harness.dataset`     | JSONL loader → `Example` objects                                |
| `eval_harness.targets`     | `mock` (deterministic) and `http` (POST `{"input":...}`)        |
| `eval_harness.judges`      | Built-in kinds: exact_match, contains, regex, length, latency, cost |
| `eval_harness.runner`      | Orchestrate: dataset × target × judges → `RunResult`            |
| `eval_harness.diff`        | Compare two `RunResult`s with direction-aware guards            |
| `eval_harness.renderer`    | Markdown PR-comment renderer (compact, GitHub-friendly)         |
| `eval_harness.cli`         | `run`, `diff`, `comment` subcommands                            |
| `action.yml`               | Composite GitHub Action wrapping the CLI                        |

## Key Design Decisions

### 1. Three CLI subcommands, not one mega-command

`run`, `diff`, and `comment` are independent steps. CI can cache the head Result, fan-out diffs against multiple baselines, or re-render the comment without re-running the eval. This is the same shape as `pytest` → `coverage` → `coverage report`.

### 2. Direction-aware guards

`higher_is_better=True` means a regression is a *decrease* (accuracy, faithfulness). `higher_is_better=False` means a regression is an *increase* (cost, latency). One model handles both quality and cost regressions without ad-hoc per-metric logic.

### 3. Tolerance lives on the guard, not the metric

`max_delta` is the absolute change a metric is allowed to move in the wrong direction before it counts as a regression. Suites can be conservative for accuracy (`max_delta: 0.01`) and lax for cost (`max_delta: 0.001`).

### 4. Separate `RunResult` from raw verdicts

The on-disk `Result JSON` only contains aggregate `MetricStats`. Per-example verdicts stay in memory. Baselines are small, content-stable, and cheap to commit if needed.

### 5. Targets and judges are tiny protocols

A target is "give it an `Example`, get a `Prediction`." A judge is "give it an `Example` + `Prediction`, get a `Verdict`." Plugging in a Vertex AI or Bedrock target is a 30-line file. LLM-as-a-judge is the same.

### 6. The Action is composite, not Docker

Composite actions are fast (no image build/pull) and leverage `actions/setup-python` cache. The CLI is just `pip install`'d from the tagged ref of this repo.

## Trade-offs Recorded for v0.2

- **No statistical power tests yet.** The runner does not warn when the dataset is too small to detect the configured `max_delta`. v0.2 will compute confidence intervals via bootstrapping.
- **No content-addressed caching.** Two identical runs do double the work. v0.2 will cache `(dataset_hash, target_id, judge_set_hash)` → result.
- **No LLM-as-a-judge built-ins.** The framework supports them via the protocol; v0.2 will ship faithfulness, toxicity, helpfulness as drop-in kinds.

## Operational Targets (v0.1)

- CLI cold-start: ≤ 2s
- 1k examples × 4 judges with `mock` target: ≤ 5s
- Test coverage on `src/eval_harness/`: ≥ 85%
- Action wall-clock for the example suite (5 examples): ≤ 30s on `ubuntu-latest`

## Extension Points

- `targets.build_target` — register a new target kind
- `judges.build_judge` — register a new judge kind
- `renderer.render_pr_comment` — swap the Markdown template (e.g., for Slack)
