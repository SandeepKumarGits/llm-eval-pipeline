import pytest
from deepeval import assert_test
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase


@pytest.mark.parametrize("index", range(10))
def test_faithfulness(test_cases: list[LLMTestCase], index: int):
    metric = FaithfulnessMetric(threshold=0.7, model="gemini/gemini-2.0-flash")
    assert_test(test_cases[index], [metric])
