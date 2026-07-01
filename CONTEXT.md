# Session Context — LLM Eval Pipeline

Complete context for continuing work on this project in another AI assistant.

---

## What This Project Is

A CI/CD pipeline capstone that deploys a containerized LLM application to Google Cloud Run and runs automated rubric-based evaluations using DeepEval. The focus is on **pipeline infrastructure and eval automation**, not app complexity.

**Live URL:** https://grounded-qa-dltluc3xzq-uc.a.run.app  
**GitHub:** https://github.com/SandeepKumarGits/llm-eval-pipeline  
**Owner:** Sandeep Kumar (krsandeep98@gmail.com)

---

## Architecture

```
Push to main → Unit Tests → Docker Build → Push to Artifact Registry → Deploy to Cloud Run → DeepEval Suite → Pass/Fail
```

The app is a **Grounded Q&A API** — it takes a question + context, calls Gemini Flash, and returns an answer strictly grounded in the provided context. This makes DeepEval metrics (faithfulness, relevance, hallucination) meaningful.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Python 3.12+, FastAPI, Uvicorn |
| LLM | Google Gemini 2.0 Flash (REST API, no SDK) |
| Evaluation | DeepEval (LLM-as-judge with Gemini) |
| Resilience | Tenacity (exponential backoff on 429/5xx) |
| Container | Docker multi-stage build |
| CI/CD | GitHub Actions (3 jobs: test → build-deploy → evaluate) |
| Cloud | Google Cloud Run + Artifact Registry (us-central1) |
| Frontend | Vanilla HTML playground (served from static/) |

---

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Interactive web playground |
| `/health` | GET | Health check + active model |
| `/ask` | POST | Grounded Q&A (question + context → answer) |
| `/evaluate` | POST | Inline DeepEval scoring (question + answer + context → metric scores) |

---

## Project Structure

```
llm-eval-pipeline/
├── src/grounded_qa/
│   ├── main.py              # FastAPI app with all endpoints
│   ├── llm.py               # Gemini client with tenacity retry
│   ├── models.py            # Pydantic schemas (AskRequest, AskResponse)
│   └── static/index.html    # Web playground UI
├── evals/
│   ├── conftest.py          # Fixtures: calls live endpoint, builds LLMTestCases
│   ├── dataset.json         # 10 test cases (question, context, expected_output)
│   ├── test_faithfulness.py # FaithfulnessMetric (threshold 0.7)
│   ├── test_relevance.py    # AnswerRelevancyMetric (threshold 0.7)
│   └── test_hallucination.py# HallucinationMetric (threshold 0.5)
├── tests/
│   └── test_main.py         # Unit tests (mocked, no API key needed)
├── .github/workflows/
│   └── deploy-and-eval.yml  # CI/CD pipeline
├── Dockerfile
├── pyproject.toml
├── next_steps_and_pitch.md  # Roadmap + interview talking points
└── .env.example
```

---

## Environment Variables

| Variable | Default | Where |
|----------|---------|-------|
| `GEMINI_API_KEY` | (required) | .env locally, GitHub Secret in CI |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Can override to test other models |
| `PORT` | `8080` | Cloud Run sets this automatically |
| `SERVICE_URL` | `http://localhost:8080` | Used by eval suite to target endpoint |

---

## GitHub Secrets (already configured)

- `GCP_PROJECT_ID` = `llm-eval-pipeline`
- `GCP_SA_KEY` = service account JSON (github-deployer@llm-eval-pipeline.iam.gserviceaccount.com)
- `GEMINI_API_KEY` = Google AI Studio key

---

## GCP Setup

- **Project:** `llm-eval-pipeline`
- **Region:** us-central1
- **Artifact Registry:** `us-central1-docker.pkg.dev/llm-eval-pipeline/llm-eval-pipeline/grounded-qa`
- **Cloud Run service:** `grounded-qa`
- **Service account:** `github-deployer` with roles: run.admin, artifactregistry.writer, iam.serviceAccountUser

---

## Current State (as of July 2026)

### What's Working
- Unit tests pass in CI ✓
- Docker builds and pushes to Artifact Registry ✓
- Cloud Run deploys successfully ✓
- Health endpoint responds ✓
- `--allow-unauthenticated` configured ✓
- Web playground UI serves ✓

### What's Pending
- **Gemini API quota:** The free tier quota was exhausted (429 errors). Once it resets, `/ask` and the eval suite will work. Just re-trigger: `git commit --allow-empty -m "retry" && git push origin master:main`
- **Security:** API key and GCP service account key were shared in chat — need to rotate both after confirming pipeline works end-to-end

---

## CI/CD Pipeline (`.github/workflows/deploy-and-eval.yml`)

```
Trigger: push to main (or PR for test job only)

Job 1: test
  - Python 3.12, pip install -e ".[dev]", pytest tests/ -v
  - Fast, no secrets needed

Job 2: build-deploy (needs: test, only on push to main)
  - Auth to GCP → configure Docker → build & push image → deploy Cloud Run
  - Outputs: service_url

Job 3: evaluate (needs: build-deploy)
  - pip install -e . → deepeval test run evals/
  - Uses SERVICE_URL from deploy output + GEMINI_API_KEY
  - Uploads .deepeval/ as artifact
```

---

## Key Design Decisions

1. **REST API for Gemini (not SDK):** Keeps the dependency minimal and mirrors how stock-sage does it. Direct HTTP calls with httpx.
2. **DeepEval with Gemini-as-judge:** All free. The same model judges its own outputs — slightly circular but $0 cost.
3. **Retry with tenacity:** Free tier Gemini aggressively rate-limits. Exponential backoff (2s→4s→8s→10s max, 5 attempts) handles 429s gracefully.
4. **Session-scoped fixtures in conftest:** Calls the endpoint once per test run (not per metric), avoiding 30 separate API calls for 10 cases × 3 metrics.
5. **Dynamic parametrize:** Test count derives from `len(load_dataset())`, so adding test cases = just appending to dataset.json.

---

## Next Steps (from next_steps_and_pitch.md)

### High Priority
1. ~~Push to GitHub~~ ✓
2. ~~Wire up pipeline end-to-end~~ ✓ (pending quota reset)
3. Add eval history dashboard (`/history` page showing score trends)

### Medium Priority
4. Add more eval metrics (toxicity, bias, custom rubrics)
5. Parameterize system prompt in playground UI
6. Batch eval mode (upload CSV, run all, download report)
7. Structured logging + OpenTelemetry traces

### Nice-to-Have
8. Multi-model comparison (side-by-side eval scores)
9. Cost/token tracking per request
10. GitHub PR comment bot (post eval scores on PRs)

---

## How to Run Locally

```bash
cd ~/projects/llm-eval-pipeline
source .venv/Scripts/activate   # Windows Git Bash
# .env file already has GEMINI_API_KEY set

# Start app
uvicorn grounded_qa.main:app --reload --port 8080
# Open http://localhost:8080 for playground

# Unit tests (no API key needed)
pytest tests/ -v

# Eval suite (needs running app + API key)
export SERVICE_URL=http://localhost:8080
deepeval test run evals/
```

---

## Git History

```
3d7ede5 Fix Cloud Run deploy: allow unauthenticated access
9a1b48d trigger full CI/CD pipeline
a1595ed Add unit test CI job, update README, fix Dockerfile PORT handling
d8cbeba Add project pitch guide and next steps roadmap
34be3f6 Add web playground, inline eval endpoint, retry logic, and unit tests
f9afd0d Initial scaffold: CI/CD pipeline for LLM evaluation
```

---

## Interview Talking Points

- **Why this exists:** Traditional tests are deterministic (`f(x) == y`). LLMs are non-deterministic — you need a different quality gate. This integrates LLM evaluation into standard CI/CD.
- **Engineering challenges:** Rate limiting (solved with retry), environment portability (env vars everywhere), test scalability (dataset-driven parametrize).
- **What it demonstrates:** CI/CD design, containerization, cloud deployment, API design, LLM evaluation, retry patterns, test automation.
