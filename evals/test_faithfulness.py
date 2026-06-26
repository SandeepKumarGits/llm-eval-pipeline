import os
import pytest
from deepeval import assert_test
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase
from conftest import load_dataset

dataset_len = len(load_dataset())


@pytest.mark.parametrize("index", range(dataset_len))
def test_faithfulness(test_cases: list[LLMTestCase], index: int):
    active_model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    metric = FaithfulnessMetric(threshold=0.7, model=f"gemini/{active_model}")
    assert_test(test_cases[index], [metric])
