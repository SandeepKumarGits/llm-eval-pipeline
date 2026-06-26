import logging
import os
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception, before_sleep_log

logger = logging.getLogger("grounded_qa.llm")

# Default model, kept as module constant for backwards compatibility
GEMINI_MODEL = "gemini-2.0-flash"

SYSTEM_PROMPT = (
    "You are a precise Q&A assistant. Answer the user's question using ONLY the provided context. "
    "Do not use any outside knowledge. If the answer cannot be found in the context, "
    "respond with: 'The answer is not available in the provided context.'"
)

def is_transient_error(exception: Exception) -> bool:
    if isinstance(exception, httpx.HTTPStatusError):
        # Retry on Rate Limit (429) or Server Errors (5xx)
        return exception.response.status_code == 429 or exception.response.status_code >= 500
    if isinstance(exception, (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)):
        return True
    return False

@retry(
    retry=retry_if_exception(is_transient_error),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
async def _execute_gemini_call(client: httpx.AsyncClient, url: str, headers: dict, json: dict) -> httpx.Response:
    response = await client.post(url, headers=headers, json=json)
    response.raise_for_status()
    return response

async def generate_answer(question: str, context: str) -> str:
    api_key = os.environ["GEMINI_API_KEY"]
    model = os.environ.get("GEMINI_MODEL", GEMINI_MODEL)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"Context:\n{context}\n\n"
                            f"Question: {question}\n\n"
                            "Answer:"
                        )
                    }
                ]
            }
        ],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await _execute_gemini_call(
            client,
            url,
            headers={"X-goog-api-key": api_key},
            json=payload
        )

    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()

