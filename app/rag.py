from search import search
from reranker import rerank

import requests


def build_context(query: str):

    chunks = search(query, top_k=10)

    seen = set()
    unique = []

    for c in chunks:

        norm = " ".join(c.split())

        if norm not in seen:
            seen.add(norm)
            unique.append(c)

    top_chunks = rerank(
        query=query,
        chunks=unique,
        top_k=5
    )

    return "\n\n".join(top_chunks)


def generate_answer(query: str, context: str):

    if not context.strip():
        return "Нет данных"

    prompt = f"""
Ты — система извлечения фактов из документа.

ЗАПРЕЩЕНО:
- придумывать информацию
- объяснять
- интерпретировать

РАЗРЕШЕНО:
- копировать фрагменты текста
- кратко извлекать ответ

Если ответа нет — пиши: "Нет данных"

КОНТЕКСТ:
{context}

ВОПРОС:
{query}

ОТВЕТ (строго из текста):
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "temperature": 0.0
        }
    )

    return response.json()["response"]