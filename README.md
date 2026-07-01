# LLM Eval Pipeline

A CI/CD pipeline that automatically deploys a containerized LLM application to Google Cloud Run and runs an automated, rubric-based evaluation suite against it using DeepEval.

## Architecture

```
┌─────────┐     ┌──────────┐     ┌───────────────┐     ┌───────────┐     ┌──────────┐     ┌────────┐
│  Push   │────▶│   Unit   │────▶│  Build Image  │────▶│  Deploy   │────▶│ Evaluate │────▶│ Report │
│ to main │     │  Tests   │     │  to Artifact  │     │  to Cloud │     │  with    │     │ Pass / │
│         │     │          │     │  Registry     │     │  Run      │     │ DeepEval │     │ Fail   │
└─────────┘     └──────────┘     └───────────────┘     └───────────┘     └──────────┘     └────────┘
```

## What This Demonstrates

- **CI/CD**: GitHub Actions pipeline with multi-job orchestration (test → build → deploy → eval)
- **Containerization**: Multi-stage Docker build for a Python API
- **LLM Integration**: Gemini Flash for grounded question answering with retry/backoff
- **Automated Evaluation**: DeepEval metrics (faithfulness, relevance, hallucination) with LLM-as-judge
- **Cloud Deployment**: Google Cloud Run with Artifact Registry
- **Resilience**: Exponential backoff retry on transient errors (429 rate limits, 5xx server errors)

## The Application

A FastAPI service that answers questions **grounded in provided context** using Google Gemini Flash. The app enforces that answers come only from the provided context — if the answer isn't there, it says so.

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Interactive web playground for testing Q&A |
| `/health` | GET | Health check (returns status + active model) |
| `/ask` | POST | Ask a question given context → get grounded answer |
| `/evaluate` | POST | Run DeepEval metrics on a Q&A pair inline |

### Example: Ask

```bash
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "When was Acme founded?", "context": "Acme Corp was founded in 1998 by Jane Smith."}'
```

```json
{"answer": "Acme Corp was founded in 1998.", "model": "gemini-2.0-flash"}
```

### Example: Evaluate

```bash
curl -X POST http://localhost:8080/evaluate \
  -H "Content-Type: application/json" \
  -d '{"question": "When was Acme founded?", "answer": "Acme Corp was founded in 1998.", "context": "Acme Corp was founded in 1998 by Jane Smith."}'
```

```json
{
  "faithfulness": {"score": 1.0, "threshold": 0.7, "reason": "...", "success": true},
  "relevance": {"score": 0.9, "threshold": 0.7, "reason": "...", "success": true},
  "hallucination": {"score": 0.0, "threshold": 0.5, "reason": "...", "success": true}
}
```

## Evaluation Metrics

| Metric | What It Measures | Threshold | Interpretation |
|--------|-----------------|-----------|----------------|
| **Faithfulness** | Does the answer stick to the provided context? | 0.7 | Higher = more faithful |
| **Answer Relevancy** | Does it actually answer the question asked? | 0.7 | Higher = more relevant |
| **Hallucination** | Does it fabricate information not in the context? | 0.5 | Lower score = less hallucination |

All metrics use Gemini as the judge model (LLM-as-judge pattern). The evaluation can be run:
- **Inline** via the `/evaluate` endpoint (for the playground UI)
- **As a test suite** via `deepeval test run evals/` (for CI/CD)

## Quick Start (Local Development)

```bash
# Clone and set up
git clone https://github.com/krsandeep98/llm-eval-pipeline.git
cd llm-eval-pipeline

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv/Scripts/activate on Windows

# Install dependencies
pip install -e ".[dev]"

# Set your API key
export GEMINI_API_KEY="your-key-here"

# Run the app
uvicorn grounded_qa.main:app --reload --port 8080

# Open http://localhost:8080 for the web playground

# Run unit tests (no API key needed)
pytest tests/ -v

# Run eval suite (requires API key + running app)
export SERVICE_URL=http://localhost:8080
deepeval test run evals/
```

## Docker

```bash
docker build -t grounded-qa .
docker run -p 8080:8080 -e GEMINI_API_KEY="your-key" grounded-qa
```

## Pipeline

The GitHub Actions workflow (`.github/workflows/deploy-and-eval.yml`) runs on every push to `main`:

1. **Test** — Runs unit tests (fast, no API key needed)
2. **Build & Deploy** — Builds Docker image, pushes to Artifact Registry, deploys to Cloud Run
3. **Evaluate** — Runs the DeepEval suite against the live endpoint, uploads results as artifacts

The pipeline fails if unit tests fail OR any evaluation metric drops below its threshold.

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `GEMINI_API_KEY` | (required) | Google AI Studio API key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Which Gemini model to use |
| `PORT` | `8080` | Server port (Cloud Run sets this) |
| `SERVICE_URL` | `http://localhost:8080` | Target URL for eval suite |

## GCP Setup

1. Create a GCP project and enable Cloud Run + Artifact Registry APIs
2. Create an Artifact Registry Docker repository:
   ```bash
   gcloud artifacts repositories create llm-eval-pipeline \
     --repository-format=docker \
     --location=us-central1
   ```
3. Create a service account with these roles:
   - `roles/run.admin`
   - `roles/artifactregistry.writer`
   - `roles/iam.serviceAccountUser`
4. Export the service account key JSON

## GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `GCP_PROJECT_ID` | Your Google Cloud project ID |
| `GCP_SA_KEY` | Service account key JSON |
| `GEMINI_API_KEY` | Google AI Studio API key |

## Project Structure

```
llm-eval-pipeline/
├── src/grounded_qa/
│   ├── main.py              # FastAPI app — /ask, /evaluate, /health, / (playground)
│   ├── llm.py               # Gemini API client with retry logic
│   ├── models.py            # Pydantic request/response schemas
│   └── static/index.html    # Web playground UI
├── evals/
│   ├── conftest.py          # Test fixtures — calls live endpoint, builds LLMTestCases
│   ├── dataset.json         # 10 test cases (question, context, expected_output)
│   ├── test_faithfulness.py # Faithfulness metric assertions
│   ├── test_relevance.py    # Answer relevancy metric assertions
│   └── test_hallucination.py# Hallucination metric assertions
├── tests/
│   └── test_main.py         # Unit tests (mocked, no API key needed)
├── .github/workflows/
│   └── deploy-and-eval.yml  # CI/CD pipeline
├── Dockerfile               # Multi-stage build
├── pyproject.toml           # Dependencies and project config
└── .env.example             # Template for local env vars
```

## Tech Stack

- **Runtime**: Python 3.12+, FastAPI, Uvicorn
- **LLM**: Google Gemini 2.0 Flash (via REST API)
- **Evaluation**: DeepEval (faithfulness, relevance, hallucination metrics)
- **Resilience**: Tenacity (retry with exponential backoff)
- **Container**: Docker multi-stage build
- **CI/CD**: GitHub Actions
- **Cloud**: Google Cloud Run + Artifact Registry
