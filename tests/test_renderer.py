from eval_harness.diff import MetricDelta
from eval_harness.renderer import render_pr_comment


def test_render_includes_table_and_status():
    deltas = [
        MetricDelta(metric="acc", head=0.92, baseline=0.90, delta=0.02, higher_is_better=True, regression=False, improvement=True),
        MetricDelta(metric="cost_usd", head=0.0009, baseline=0.0010, delta=-0.0001, higher_is_better=False, regression=False, improvement=True),
    ]
    md = render_pr_comment(deltas, "demo", head_sha="abc12345deadbeef")
    assert "eval-harness-pro" in md
    assert "| Metric |" in md
    assert "improvement" in md
    assert "abc12345" in md
    assert "All guards passed." in md


def test_render_flags_regression_and_blocks_merge():
    deltas = [
        MetricDelta(metric="acc", head=0.80, baseline=0.90, delta=-0.10, higher_is_better=True, regression=True, improvement=False),
    ]
    md = render_pr_comment(deltas, "demo")
    assert "Merge blocked" in md
    assert "regression" in md


def test_render_handles_empty_metrics():
    md = render_pr_comment([], "demo")
    assert "No metrics produced" in md
