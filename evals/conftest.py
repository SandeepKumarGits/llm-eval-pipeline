import json
import os
import time
from pathlib import Path

import httpx
import pytest
from deepeval.test_case import LLMTestCase

DATASET_PATH = Path(__file__).parent / "dataset.json"


def get_service_url() -> str:
    url = os.environ.get("SERVICE_URL", "http://localhost:8080")
    return url.rstrip("/")


def load_dataset() -> list[dict]:
    with open(DATASET_PATH) as f:
        return json.load(f)


def call_endpoint(question: str, context: str) -> str:
    url = f"{get_service_url()}/ask"
    response = httpx.post(url, json={"question": question, "context": context}, timeout=30.0)
    response.raise_for_status()
    return response.json()["answer"]


@pytest.fixture(scope="session")
def test_cases() -> list[LLMTestCase]:
    dataset = load_dataset()
    cases = []
    for i, item in enumerate(dataset):
        if i > 0:
            time.sleep(5)
        actual_output = call_endpoint(item["question"], item["context"])
        cases.append(
            LLMTestCase(
                input=item["question"],
                actual_output=actual_output,
                expected_output=item["expected_output"],
                retrieval_context=[item["context"]],
            )
        )
    return cases
