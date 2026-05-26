from search import search
from reranker import rerank
import requests


def build_context(query: str):

    chunks = search(query, top_k=10)
    top_chunks = rerank(query, chunks, top_k=3)

    return "\n\n".join(top_chunks)


def generate_answer(query: str, context: str):

    prompt = f"""
Ты отвечаешь строго по контексту.

Если ответа нет — скажи "нет данных".

КОНТЕКСТ:
{context}

ВОПРОС:
{query}

ОТВЕТ:
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "temperature": 0.1
        }
    )

    return response.json()["response"]