import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


@pytest.mark.parametrize("index", range(10))
def test_answer_relevancy(test_cases: list[LLMTestCase], index: int):
    metric = AnswerRelevancyMetric(threshold=0.7, model="gemini/gemini-2.0-flash")
    assert_test(test_cases[index], [metric])
