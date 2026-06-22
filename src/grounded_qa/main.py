import os

from fastapi import FastAPI, HTTPException

from grounded_qa.llm import generate_answer, GEMINI_MODEL
from grounded_qa.models import AskRequest, AskResponse

app = FastAPI(title="Grounded Q&A", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    try:
        answer = await generate_answer(request.question, request.context)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc}")
    return AskResponse(answer=answer, model=GEMINI_MODEL)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
