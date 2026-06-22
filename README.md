# LLM Eval Pipeline

A CI/CD pipeline that automatically deploys a containerized LLM application to Google Cloud Run and runs an automated, rubric-based evaluation suite against it using DeepEval.

## Architecture

```
┌─────────┐     ┌───────────────┐     ┌───────────┐     ┌──────────┐     ┌────────┐
│  Push   │────▶│  Build Image  │────▶│  Deploy   │────▶│ Evaluate │────▶│ Report │
│ to main │     │  to Artifact  │     │  to Cloud │     │  with    │     │ Pass / │
│         │     │  Registry     │     │  Run      │     │ DeepEval │     │ Fail   │
└─────────┘     └───────────────┘     └───────────┘     └──────────┘     └────────┘
```

## What This Demonstrates

- **CI/CD**: GitHub Actions pipeline with multi-job orchestration
- **Containerization**: Multi-stage Docker build for a Python API
- **LLM Integration**: Gemini Flash for grounded question answering
- **Automated Evaluation**: DeepEval metrics (faithfulness, relevance, hallucination) with LLM-as-judge
- **Cloud Deployment**: Google Cloud Run with Artifact Registry

## The Application

A FastAPI service that answers questions **grounded in provided context** using Google Gemini Flash. It's intentionally simple — the focus is on the infrastructure around it.

```bash
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "When was Acme founded?", "context": "Acme Corp was founded in 1998 by Jane Smith."}'
```

```json
{"answer": "Acme Corp was founded in 1998.", "model": "gemini-2.0-flash"}
```

## Evaluation Metrics

| Metric | What It Measures | Threshold |
|--------|-----------------|-----------|
| **Faithfulness** | Does the answer stick to the provided context? | 0.7 |
| **Answer Relevancy** | Does it actually answer the question asked? | 0.7 |
| **Hallucination** | Does it fabricate information not in the context? | 0.5 |

All metrics use Gemini as the judge model (LLM-as-judge pattern).

## Quick Start (Local Development)

```bash
# Clone and set up
git clone https://github.com/YOUR_USERNAME/llm-eval-pipeline.git
cd llm-eval-pipeline

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv/Scripts/activate on Windows

# Install dependencies
pip install -e ".[eval]"

# Set your API key
export GEMINI_API_KEY="your-key-here"

# Run the app
uvicorn grounded_qa.main:app --reload --port 8080

# Run evals (in another terminal)
export SERVICE_URL=http://localhost:8080
export GEMINI_API_KEY="your-key-here"
deepeval test run evals/
```

## Docker

```bash
docker build -t grounded-qa .
docker run -p 8080:8080 -e GEMINI_API_KEY="your-key" grounded-qa
```

## Pipeline

The GitHub Actions workflow (`.github/workflows/deploy-and-eval.yml`) runs on every push to `main`:

1. **Build & Deploy** — Builds the Docker image, pushes to Artifact Registry, deploys to Cloud Run
2. **Evaluate** — Installs DeepEval, runs the eval suite against the live endpoint, uploads results as artifacts

The pipeline fails if any evaluation metric drops below its threshold.

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

## Tech Stack

- **Runtime**: Python 3.12, FastAPI, Uvicorn
- **LLM**: Google Gemini 2.0 Flash
- **Evaluation**: DeepEval (faithfulness, relevance, hallucination metrics)
- **Container**: Docker multi-stage build
- **CI/CD**: GitHub Actions
- **Cloud**: Google Cloud Run + Artifact Registry
