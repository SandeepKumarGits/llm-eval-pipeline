import os
from typing import Optional

from dotenv import load_dotenv
# Load environment variables from .env file before anything else imports them
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric, HallucinationMetric
from deepeval.test_case import LLMTestCase

from grounded_qa.llm import generate_answer, GEMINI_MODEL
from grounded_qa.models import AskRequest, AskResponse

app = FastAPI(title="Grounded Q&A", version="0.1.0")


class EvalRequest(BaseModel):
    question: str
    answer: str
    context: str


class MetricResult(BaseModel):
    score: float
    threshold: float
    reason: Optional[str] = None
    success: bool


class EvalResponse(BaseModel):
    faithfulness: MetricResult
    relevance: MetricResult
    hallucination: MetricResult


@app.get("/health")
async def health():
    active_model = os.environ.get("GEMINI_MODEL", GEMINI_MODEL)
    return {"status": "healthy", "model": active_model}


@app.get("/", response_class=HTMLResponse)
def get_playground():
    static_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(static_dir, "static", "index.html")
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="Playground interface not found")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    try:
        answer = await generate_answer(request.question, request.context)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc}")
    active_model = os.environ.get("GEMINI_MODEL", GEMINI_MODEL)
    return AskResponse(answer=answer, model=active_model)


@app.post("/evaluate", response_model=EvalResponse)
def evaluate(request: EvalRequest):
    try:
        active_model = os.environ.get("GEMINI_MODEL", GEMINI_MODEL)
        eval_model = f"gemini/{active_model}"

        test_case = LLMTestCase(
            input=request.question,
            actual_output=request.answer,
            retrieval_context=[request.context],
        )

        # 1. Faithfulness Metric (Checks if response stays within context)
        faithfulness_metric = FaithfulnessMetric(threshold=0.7, model=eval_model)
        faithfulness_metric.measure(test_case)

        # 2. Answer Relevancy Metric (Checks if response directly answers the question)
        relevancy_metric = AnswerRelevancyMetric(threshold=0.7, model=eval_model)
        relevancy_metric.measure(test_case)

        # 3. Hallucination Metric (Checks if response contains fabricated info)
        hallucination_metric = HallucinationMetric(threshold=0.5, model=eval_model)
        hallucination_metric.measure(test_case)

        return EvalResponse(
            faithfulness=MetricResult(
                score=faithfulness_metric.score,
                threshold=faithfulness_metric.threshold,
                reason=faithfulness_metric.reason,
                success=faithfulness_metric.is_successful(),
            ),
            relevance=MetricResult(
                score=relevancy_metric.score,
                threshold=relevancy_metric.threshold,
                reason=relevancy_metric.reason,
                success=relevancy_metric.is_successful(),
            ),
            hallucination=MetricResult(
                score=hallucination_metric.score,
                threshold=hallucination_metric.threshold,
                reason=hallucination_metric.reason,
                success=hallucination_metric.is_successful(),
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Evaluation failed: {exc}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)

