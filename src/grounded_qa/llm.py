import os

import httpx

GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
)

SYSTEM_PROMPT = (
    "You are a precise Q&A assistant. Answer the user's question using ONLY the provided context. "
    "Do not use any outside knowledge. If the answer cannot be found in the context, "
    "respond with: 'The answer is not available in the provided context.'"
)


async def generate_answer(question: str, context: str) -> str:
    api_key = os.environ["GEMINI_API_KEY"]

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
        response = await client.post(
            GEMINI_URL,
            headers={"X-goog-api-key": api_key},
            json=payload,
        )
        response.raise_for_status()

    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
