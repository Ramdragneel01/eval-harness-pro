# Contributing to eval-harness-pro

## Local Setup

```bash
git clone https://github.com/Ramdragneel01/eval-harness-pro.git
cd eval-harness-pro
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
pytest
```

## Branching & Commits

- Branch from `main`: `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>`.
- Use [Conventional Commits](https://www.conventionalcommits.org/).
- One logical change per PR.

## What Gets Reviewed

Every PR must:
1. Pass `ruff check src tests`.
2. Pass `pytest`.
3. Add or update tests for any behavior change.
4. Update `CHANGELOG.md` under "Unreleased" if user-visible.
5. Include a sample suite + diff in the PR description for new judge or target kinds.

## Adding a New Judge Kind

1. Add the function in `src/eval_harness/judges.py` and wire it into `build_judge`.
2. Update the `JudgeSpec.kind` Literal in `src/eval_harness/schema.py`.
3. Add at least one passing and one failing test in `tests/test_judges.py`.
4. Document the kind in `README.md` and `ARCHITECTURE.md`.

## Adding a New Target Kind

1. Implement the `Target` protocol in `src/eval_harness/targets.py`.
2. Wire it into `build_target` and add a `TargetSpec.kind` Literal.
3. Cover the happy path in `tests/test_runner.py` (use `respx` if it's HTTP-based).

## Reporting Bugs

Use the GitHub issue tracker for non-security bugs. For security issues, see [SECURITY.md](SECURITY.md).
