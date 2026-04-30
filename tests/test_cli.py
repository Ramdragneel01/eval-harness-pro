"""End-to-end CLI tests using Click's CliRunner."""
from pathlib import Path

from click.testing import CliRunner

from eval_harness.cli import main

REPO_ROOT = Path(__file__).resolve().parent.parent


def _write_local_suite(tmp_path: Path) -> Path:
    suite = tmp_path / "suite.yaml"
    suite.write_text(
        f"""
name: cli-suite
target:
  kind: mock
dataset:
  path: {REPO_ROOT.as_posix()}/examples/dataset.jsonl
judges:
  - {{ name: exact_match, kind: exact_match }}
  - {{ name: latency_ms,  kind: latency, threshold: 100 }}
guards:
  - {{ metric: exact_match, higher_is_better: true,  max_delta: 0.05 }}
  - {{ metric: latency_ms,  higher_is_better: false, max_delta: 25 }}
""",
        encoding="utf-8",
    )
    return suite


def test_run_diff_comment_pipeline(tmp_path: Path):
    runner = CliRunner()
    suite = _write_local_suite(tmp_path)
    head_out = tmp_path / "head.json"
    baseline_out = tmp_path / "baseline.json"
    diff_out = tmp_path / "diff.json"
    comment_out = tmp_path / "comment.md"

    r1 = runner.invoke(main, ["run", "--suite", str(suite), "--out", str(head_out)])
    assert r1.exit_code == 0, r1.output
    r2 = runner.invoke(main, ["run", "--suite", str(suite), "--out", str(baseline_out)])
    assert r2.exit_code == 0, r2.output

    r3 = runner.invoke(
        main,
        [
            "diff",
            "--head", str(head_out),
            "--baseline", str(baseline_out),
            "--suite", str(suite),
            "--out", str(diff_out),
        ],
    )
    assert r3.exit_code == 0, r3.output  # mock vs mock = no regression
    assert diff_out.exists()

    r4 = runner.invoke(
        main,
        ["comment", "--diff", str(diff_out), "--out", str(comment_out), "--head-sha", "deadbeef"],
    )
    assert r4.exit_code == 0, r4.output
    body = comment_out.read_text(encoding="utf-8")
    assert "eval-harness-pro" in body
    assert "cli-suite" in body


def test_diff_exits_nonzero_on_regression(tmp_path: Path):
    runner = CliRunner()
    suite = _write_local_suite(tmp_path)
    head_out = tmp_path / "head.json"
    baseline_out = tmp_path / "baseline.json"
    diff_out = tmp_path / "diff.json"

    runner.invoke(main, ["run", "--suite", str(suite), "--out", str(head_out)])
    # Hand-craft a baseline with a much better metric so head looks like a regression.
    baseline_out.write_text(
        '{"suite":"cli-suite","n_examples":5,"metrics":{"exact_match":{"metric":"exact_match","mean":1.5,"pass_rate":1.0,"n":5},"latency_ms":{"metric":"latency_ms","mean":5.0,"pass_rate":1.0,"n":5}},"metadata":{}}',
        encoding="utf-8",
    )
    r = runner.invoke(
        main,
        [
            "diff",
            "--head", str(head_out),
            "--baseline", str(baseline_out),
            "--suite", str(suite),
            "--out", str(diff_out),
        ],
    )
    assert r.exit_code == 1, r.output
