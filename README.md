# eval-harness-pro

> **Continuous evaluation CI for LLM applications.** Declarative YAML eval suites + a GitHub Action that runs them on every PR, diffs against a baseline, posts a Markdown comment, and blocks merge on regressions.

[![CI](https://github.com/Ramdragneel01/eval-harness-pro/actions/workflows/ci.yml/badge.svg)](https://github.com/Ramdragneel01/eval-harness-pro/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

---

## Why

LLM apps drift silently. A new model snapshot, a "small" prompt tweak, a chunk-size change — any of these can quietly tank quality, raise cost, or balloon latency without breaking a single unit test. `eval-harness-pro` brings evals into the place engineers already look: the pull request.

## Pipeline at a glance

```
suite.yaml ──► eval-harness run ──► head.json
                                       │
baseline.json (from main) ────────────►│ eval-harness diff ──► diff.json ──► PR comment
                                                                                │
                                                            ▲                   ▼
                                                            └── fail merge on regression
```

## Quickstart — local

```bash
pip install eval-harness-pro
eval-harness run --suite examples/suite.yaml --out head.json
eval-harness diff --suite examples/suite.yaml --head head.json --out diff.json
eval-harness comment --diff diff.json --out comment.md --head-sha "$(git rev-parse HEAD)"
cat comment.md
```

## Quickstart — GitHub Action

```yaml
# .github/workflows/eval.yml
name: eval
on:
  pull_request:
    branches: [main]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Pull the latest baseline produced on main (uploaded by a separate workflow).
      - name: Download baseline
        uses: actions/download-artifact@v4
        with:
          name: eval-baseline
          path: baseline
        continue-on-error: true

      - uses: Ramdragneel01/eval-harness-pro@v0.1.0
        id: eval
        with:
          suite: evals/suite.yaml
          baseline: baseline/head.json
          head_sha: ${{ github.sha }}

      - name: Comment on PR
        uses: marocchino/sticky-pull-request-comment@v2
        with:
          path: ${{ steps.eval.outputs.comment_path }}
```

## Suite shape

```yaml
name: my-suite
target:
  kind: http              # or "mock" for self-contained tests
  url: http://localhost:8080/predict
dataset:
  path: evals/dataset.jsonl   # JSONL: {"input":"...","expected":"..."}
  limit: 200
judges:
  - { name: exact_match, kind: exact_match }
  - { name: contains,    kind: contains }
  - { name: latency_ms,  kind: latency, threshold: 800 }
  - { name: cost_usd,    kind: cost,    threshold: 0.005 }
guards:
  - { metric: exact_match, higher_is_better: true,  max_delta: 0.02 }
  - { metric: latency_ms,  higher_is_better: false, max_delta: 100 }
  - { metric: cost_usd,    higher_is_better: false, max_delta: 0.0005 }
```

Supported judge kinds out of the box: `exact_match`, `contains`, `regex`, `length`, `latency`, `cost`. Add a custom kind by editing `src/eval_harness/judges.py`.

## CLI

| Command                  | Purpose                                                  |
| ------------------------ | -------------------------------------------------------- |
| `eval-harness run`       | Execute a suite, write a Result JSON                     |
| `eval-harness diff`      | Diff a head Result against a baseline; emit a diff JSON  |
| `eval-harness comment`   | Render a Markdown PR comment from a diff JSON            |

`eval-harness diff --fail-on-regression` (default) exits with code `1` when any guard reports a regression. That is the merge-block hook.

## Design

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design, including:

- Why guards are direction-aware (regression for cost is an *increase*, regression for accuracy is a *decrease*)
- Why the runner is split from the diff engine (cacheability, replayability)
- Where to plug in a custom target, judge, or LLM-as-a-judge

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

23 tests cover schema loading, runner end-to-end, all judge kinds, the diff engine (regressions, improvements, tolerances, missing baselines), the renderer, and the full CLI pipeline.

## Roadmap

- [ ] Statistical-power warnings (suite size vs. metric variance)
- [ ] Cached runs (content-addressed by dataset + judge versions)
- [ ] LLM-as-a-judge built-ins (faithfulness, toxicity, helpfulness)
- [ ] Native integration with [`ragbench`](https://github.com/Ramdragneel01/ragbench) and [`llm-judge`](https://github.com/Ramdragneel01/llm-judge)

Part of the **Production AI, From Zero** series — see [companion Medium article](https://medium.com/@RamPrakashD).

## License

[MIT](LICENSE) © Ram Prakash Dhulipudi
