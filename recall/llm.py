from google import genai
from google.genai import types

from recall.config import Config
from recall.models import SearchResult

_NO_MEMORIES = "I don't have anything saved about that yet."

_SYSTEM_PROMPT = (
    "You are a personal memory assistant. "
    "Answer the user's question using ONLY the memories listed below. "
    "Be concise and natural. "
    "If the memories don't contain the answer, say you don't have anything saved about that. "
    "Never invent details."
)


def synthesize_answer(question: str, memories: list[SearchResult], cfg: Config) -> str:
    if not memories:
        return _NO_MEMORIES

    memory_lines = "\n".join(
        f"{i + 1}. [{r.created_at[:10]}] {r.content}"
        for i, r in enumerate(memories)
    )
    user_message = f"Memories:\n{memory_lines}\n\nQuestion: {question}"

    client = genai.Client(api_key=cfg.gemini_api_key)
    response = client.models.generate_content(
        model=cfg.chat_model,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            temperature=0.2,
        ),
    )
    return response.text.strip()
