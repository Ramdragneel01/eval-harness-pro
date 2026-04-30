from eval_harness.diff import diff_results, has_regression
from eval_harness.runner import MetricStats, RunResult
from eval_harness.schema import GuardSpec


def _result(metrics: dict[str, float]) -> RunResult:
    return RunResult(
        suite="t",
        n_examples=10,
        metrics={k: MetricStats(metric=k, mean=v, pass_rate=1.0, n=10) for k, v in metrics.items()},
    )


def test_no_baseline_yields_neutral_deltas():
    head = _result({"acc": 0.9, "latency_ms": 80})
    deltas = diff_results(head, baseline=None, guards=[
        GuardSpec(metric="acc", higher_is_better=True, max_delta=0.02),
    ])
    assert all(d.delta is None for d in deltas)
    assert has_regression(deltas) is False


def test_higher_is_better_regression_detected():
    baseline = _result({"acc": 0.90})
    head = _result({"acc": 0.80})  # dropped 10 points
    deltas = diff_results(head, baseline, [GuardSpec(metric="acc", higher_is_better=True, max_delta=0.02)])
    [acc] = [d for d in deltas if d.metric == "acc"]
    assert acc.regression is True
    assert acc.improvement is False


def test_higher_is_better_within_tolerance_is_neutral():
    baseline = _result({"acc": 0.90})
    head = _result({"acc": 0.89})  # 0.01 drop, tolerance 0.02
    deltas = diff_results(head, baseline, [GuardSpec(metric="acc", higher_is_better=True, max_delta=0.02)])
    [acc] = [d for d in deltas if d.metric == "acc"]
    assert acc.regression is False


def test_lower_is_better_regression_for_cost():
    baseline = _result({"cost_usd": 0.001})
    head = _result({"cost_usd": 0.003})
    deltas = diff_results(head, baseline, [GuardSpec(metric="cost_usd", higher_is_better=False, max_delta=0.0005)])
    [cost] = [d for d in deltas if d.metric == "cost_usd"]
    assert cost.regression is True


def test_lower_is_better_improvement_for_latency():
    baseline = _result({"latency_ms": 200})
    head = _result({"latency_ms": 100})
    deltas = diff_results(head, baseline, [GuardSpec(metric="latency_ms", higher_is_better=False, max_delta=25)])
    [lat] = [d for d in deltas if d.metric == "latency_ms"]
    assert lat.improvement is True
    assert lat.regression is False
