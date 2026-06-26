from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import pytest

from grounded_qa.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model" in data


def test_playground():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Grounded Q&A Playground" in response.text


@patch("grounded_qa.main.generate_answer", new_callable=AsyncMock)
def test_ask(mock_generate_answer):
    mock_generate_answer.return_value = "Test Answer"

    payload = {"question": "What is the key?", "context": "The key is 1234."}
    response = client.post("/ask", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Test Answer"
    assert "model" in data

    mock_generate_answer.assert_called_once_with("What is the key?", "The key is 1234.")


@patch("grounded_qa.main.generate_answer", new_callable=AsyncMock)
def test_ask_failure(mock_generate_answer):
    mock_generate_answer.side_effect = Exception("API connection timed out")

    payload = {"question": "What is the key?", "context": "The key is 1234."}
    response = client.post("/ask", json=payload)

    assert response.status_code == 502
    assert "LLM call failed" in response.json()["detail"]


@patch("grounded_qa.main.FaithfulnessMetric")
@patch("grounded_qa.main.AnswerRelevancyMetric")
@patch("grounded_qa.main.HallucinationMetric")
@patch("grounded_qa.main.LLMTestCase")
def test_evaluate(mock_test_case, mock_hallucination, mock_relevance, mock_faithfulness):
    # Set up mock metrics
    mock_f_instance = MagicMock()
    mock_f_instance.score = 0.9
    mock_f_instance.threshold = 0.7
    mock_f_instance.reason = "Stuck to context"
    mock_f_instance.is_successful.return_value = True
    mock_faithfulness.return_value = mock_f_instance

    mock_r_instance = MagicMock()
    mock_r_instance.score = 0.85
    mock_r_instance.threshold = 0.7
    mock_r_instance.reason = "Directly answered"
    mock_r_instance.is_successful.return_value = True
    mock_relevance.return_value = mock_r_instance

    mock_h_instance = MagicMock()
    mock_h_instance.score = 0.1
    mock_h_instance.threshold = 0.5
    mock_h_instance.reason = "No hallucinations"
    mock_h_instance.is_successful.return_value = True
    mock_hallucination.return_value = mock_h_instance

    payload = {
        "question": "What is the key?",
        "answer": "The key is 1234.",
        "context": "The key is 1234."
    }
    response = client.post("/evaluate", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["faithfulness"]["score"] == 0.9
    assert data["faithfulness"]["success"] is True
    assert data["faithfulness"]["reason"] == "Stuck to context"

    assert data["relevance"]["score"] == 0.85
    assert data["relevance"]["success"] is True
    assert data["relevance"]["reason"] == "Directly answered"

    assert data["hallucination"]["score"] == 0.1
    assert data["hallucination"]["success"] is True
    assert data["hallucination"]["reason"] == "No hallucinations"
