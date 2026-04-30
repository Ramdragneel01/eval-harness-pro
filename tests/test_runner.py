from pathlib import Path

from eval_harness.runner import run_suite
from eval_harness.schema import load_suite


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_load_suite_roundtrip():
    suite = load_suite(REPO_ROOT / "examples" / "suite.yaml")
    assert suite.name == "example-suite"
    assert suite.target.kind == "mock"
    assert any(j.name == "exact_match" for j in suite.judges)
    assert any(g.metric == "latency_ms" and g.higher_is_better is False for g in suite.guards)


def test_run_suite_against_mock_target_produces_metrics(tmp_path, monkeypatch):
    suite = load_suite(REPO_ROOT / "examples" / "suite.yaml")
    # Resolve dataset path relative to repo root for the test.
    suite.dataset.path = str(REPO_ROOT / suite.dataset.path)
    result = run_suite(suite)
    assert result.n_examples == 5
    assert "exact_match" in result.metrics
    # MockTarget returns expected verbatim, so exact_match must be 1.0.
    assert result.metrics["exact_match"].mean == 1.0
    assert result.metrics["latency_ms"].n == 5
