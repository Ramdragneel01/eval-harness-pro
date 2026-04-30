from eval_harness.dataset import Example
from eval_harness.judges import build_judge
from eval_harness.schema import JudgeSpec
from eval_harness.targets import Prediction


def _ex():
    return Example(input="q", expected="Paris")


def test_exact_match_passes_when_equal():
    j = build_judge(JudgeSpec(name="em", kind="exact_match"))
    v = j(_ex(), Prediction(output="Paris"))
    assert v.passed is True
    assert v.value == 1.0


def test_exact_match_fails_when_different():
    j = build_judge(JudgeSpec(name="em", kind="exact_match"))
    v = j(_ex(), Prediction(output="paris france"))
    assert v.passed is False
    assert v.value == 0.0


def test_contains_is_case_insensitive():
    j = build_judge(JudgeSpec(name="c", kind="contains"))
    v = j(_ex(), Prediction(output="The capital is paris."))
    assert v.passed is True


def test_regex_judge():
    j = build_judge(JudgeSpec(name="r", kind="regex", pattern=r"\b\d+\b"))
    v = j(_ex(), Prediction(output="There are 8 planets."))
    assert v.passed is True
    v2 = j(_ex(), Prediction(output="no digits here"))
    assert v2.passed is False


def test_latency_threshold_is_a_max():
    j = build_judge(JudgeSpec(name="lat", kind="latency", threshold=50.0))
    assert j(_ex(), Prediction(output="x", latency_ms=20.0)).passed is True
    assert j(_ex(), Prediction(output="x", latency_ms=200.0)).passed is False


def test_cost_threshold_is_a_max():
    j = build_judge(JudgeSpec(name="cost", kind="cost", threshold=0.001))
    assert j(_ex(), Prediction(output="x", cost_usd=0.0005)).passed is True
    assert j(_ex(), Prediction(output="x", cost_usd=0.01)).passed is False


def test_regex_requires_pattern():
    import pytest

    with pytest.raises(ValueError):
        build_judge(JudgeSpec(name="r", kind="regex"))
