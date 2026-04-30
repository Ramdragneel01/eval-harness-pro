# Security Policy — eval-harness-pro

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Email: **ramprakashdhulipudi@gmail.com**

Include:
- Description and impact
- Reproduction steps or proof-of-concept
- Affected version / commit SHA

We will acknowledge within 72 hours and aim to provide a remediation plan within 7 days for high-severity issues.

## Threat Model (v0.1)

### In Scope

| Class | Surface | Mitigation |
|---|---|---|
| Malicious eval suite YAML (e.g., crafted regex DoS) | `schema.load_suite` | Patterns compiled lazily; suites are operator-controlled in CI |
| Untrusted dataset JSONL | `dataset.load_examples` | Parsed with `json.loads` per line; non-object lines rejected |
| Untrusted HTTP target response | `targets.HttpTarget` | Strict schema (`output`, `cost_usd`); raises on non-2xx |
| Secret leakage in CI logs | CLI output | CLI prints filenames and counts only — never raw inputs/outputs |

### Out of Scope (v0.1)

- **Sandboxing user-provided judge code** — there is no plugin loader yet. v0.2's plugin path will document the trust boundary.
- **PR comments themselves** — comment text is generated from numeric metric values; treat the body as untrusted output if you cross-post it elsewhere.
- **Forks running with secrets** — if you wire LLM-as-a-judge with API keys, use OIDC federation; never expose secrets to PRs from forks.

## Hardening Checklist

If you wire `eval-harness-pro` into CI:

- [ ] Pin to a tagged version (`Ramdragneel01/eval-harness-pro@v0.1.0`), not `main`.
- [ ] Use OIDC + short-lived tokens for any judge that calls a paid API.
- [ ] Treat the produced `head.json` and `diff.json` as build artifacts; do not commit them to `main` blindly.
- [ ] Cap dataset size in CI to your statistical-power requirement (`dataset.limit`).
- [ ] Review changes to `evals/suite.yaml` like you review code — they govern merge gates.

## Dependency Security

- All runtime deps pinned in `requirements.txt`.
- Renovate bot enabled (planned for v0.2).
- `pip-audit` in CI (planned for v0.2).
