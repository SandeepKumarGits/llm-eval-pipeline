import pytest
from deepeval import assert_test
from deepeval.metrics import HallucinationMetric
from deepeval.test_case import LLMTestCase


@pytest.mark.parametrize("index", range(10))
def test_hallucination(test_cases: list[LLMTestCase], index: int):
    metric = HallucinationMetric(threshold=0.5, model="gemini/gemini-2.0-flash")
    assert_test(test_cases[index], [metric])
