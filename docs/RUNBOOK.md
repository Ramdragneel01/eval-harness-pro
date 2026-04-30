# Runbook — eval-harness-pro

Operational reference for teams running `eval-harness-pro` in CI.

## What it is

A non-server tool. There is no daemon, no port, no state. The CLI runs once per workflow step, reads files, writes files, and exits.

## Standard CI shape

```
on PR:
  1. checkout
  2. (optional) download baseline artifact from main
  3. eval-harness run                  # produces head.json
  4. eval-harness diff                 # produces diff.json (exits 1 on regression)
  5. eval-harness comment              # produces comment.md
  6. sticky-pull-request-comment       # post comment.md to the PR

on push to main:
  1. checkout
  2. eval-harness run                  # produces head.json
  3. upload-artifact 'eval-baseline'   # becomes the next baseline
```

## Common Operations

### Bootstrap the first baseline

The first PR after wiring the action will have `baseline = none`. The diff will report all metrics as `⚪ new`. After that PR merges to `main`, the baseline-publishing workflow uploads the artifact and subsequent PRs get green/red deltas.

### Tighten or loosen a guard

Edit `evals/suite.yaml`:

```yaml
guards:
  - { metric: faithfulness, higher_is_better: true,  max_delta: 0.01 }   # tighter
  - { metric: latency_ms,   higher_is_better: false, max_delta: 250 }    # looser
```

A tighter guard catches smaller regressions but raises false-positive risk at small `n`. A useful rule of thumb: `max_delta` should be at least `2 * stderr` of the metric on your dataset.

### Acknowledge an intentional regression

Two options:

1. Bump `max_delta` in the same PR. The reviewer sees both the suite change and the eval delta and approves once.
2. Update the baseline artifact via a manual workflow_dispatch on `main`.

### Disable for a draft PR

Add `if: github.event.pull_request.draft == false` to the workflow's job. Never disable globally.

## Alerts (suggested, for your CI dashboard)

| Alert | Condition | Severity |
|---|---|---|
| Eval suite failure spike | >25% of last 20 PRs blocked by `eval-harness-pro` | P3 |
| Eval cost spike | sum(`cost_usd`) on `main` > daily budget | P2 |
| Action wall-clock > 10m | `${{ steps.eval.outcome }}` durations rising | P3 |

## Incident Playbooks

### "All PRs are red after a model upgrade"

1. Confirm the baseline was generated on the *old* model.
2. Re-run the baseline-publishing workflow on `main` against the new model (one-time `workflow_dispatch`).
3. Resume PRs.
4. Document the model version in `evals/suite.yaml` `metadata` so the next upgrade is traceable.

### "Action passes but quality is clearly worse in production"

1. The dataset is too small or unrepresentative. Inspect `head.json` for per-metric `n` and `pass_rate`.
2. Add failing examples from production traces to the dataset.
3. Tighten the relevant guard.

### "Diff exits 1 but I cannot see why"

Run locally:
```bash
eval-harness run --suite evals/suite.yaml --out head.json
eval-harness diff --suite evals/suite.yaml --head head.json --baseline baseline.json --out diff.json --no-fail-on-regression
cat diff.json | jq '.deltas[] | select(.regression == true)'
```

## Capacity Planning

- Memory: ~50 MB.
- CPU: O(n) over dataset size; mock + simple judges run ~1k examples/sec/core.
- Disk: result/diff JSON ≤ 50 KB for typical suites (aggregates only).

## Backup / Restore

The only persisted artifact is the baseline `head.json` for `main`. Storing the last 10 baselines in artifact retention is sufficient.

## Contacts

- Maintainer: Ram Prakash Dhulipudi — ramprakashdhulipudi@gmail.com
- Security: see [SECURITY.md](../SECURITY.md)
