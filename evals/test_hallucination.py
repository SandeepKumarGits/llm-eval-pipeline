import os
import pytest
from deepeval import assert_test
from deepeval.metrics import HallucinationMetric
from deepeval.test_case import LLMTestCase
from conftest import load_dataset

dataset_len = len(load_dataset())


@pytest.mark.parametrize("index", range(dataset_len))
def test_hallucination(test_cases: list[LLMTestCase], index: int):
    active_model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    metric = HallucinationMetric(threshold=0.5, model=f"gemini/{active_model}")
    assert_test(test_cases[index], [metric])
