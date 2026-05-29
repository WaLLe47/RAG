import re
import json
import requests
from dataclasses import dataclass

from search import hybrid_search, vector_search
from reranker import rerank
from query_rewriter import rewrite_query
from qdrant_db import client, COLLECTION_NAME
from config import OLLAMA_URL, OLLAMA_MODEL

# Запросы на суммаризацию — отдельный режим с другим промптом
_SUMMARY_KEYWORDS = (
    "конспект", "перескажи", "перескажи", "краткое", "кратко",
    "резюме", "суммари", "summary", "summarize", "overview",
    "о чём", "о чем", "расскажи", "опиши документ",
)


@dataclass
class RAGAnswer:
    answer: str
    confidence: float
    raw: str


def _get_all_chunks() -> list[str]:
    results = []
    offset = None
    while True:
        resp = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=256,
            offset=offset,
            with_payload=True,
        )
        points, next_offset = resp
        results.extend(p.payload["text"] for p in points)
        if next_offset is None:
            break
        offset = next_offset
    return results


def _is_summary_request(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in _SUMMARY_KEYWORDS)


def build_context(query: str, use_hybrid: bool = True) -> str:
    rewritten = rewrite_query(query)
    print(f"[rag] rewritten: {rewritten!r}")

    if use_hybrid:
        all_chunks = _get_all_chunks()
        chunks = hybrid_search(rewritten, all_chunks, top_k=25)
    else:
        chunks = vector_search(rewritten, top_k=25)

    # Для суммаризации берём больше чанков
    top_k = 12 if _is_summary_request(query) else 8
    top = rerank(rewritten, chunks, top_k=top_k)

    seen: set[str] = set()
    cleaned: list[str] = []
    for t in top:
        t = " ".join(t.split())
        if len(t) > 30 and t not in seen:
            seen.add(t)
            cleaned.append(t)

    return "\n\n".join(cleaned)


def _parse_answer(raw: str) -> tuple[str, float]:
    """
    Надёжный парсер: 4 стратегии по убыванию надёжности.
    """
    text = raw.replace("```json", "").replace("```", "").strip()

    # Стратегия 1: полный json.loads
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        data = json.loads(text[start:end])
        return str(data.get("answer", "Нет данных")), float(data.get("confidence", 0.0))
    except Exception:
        pass

    # Стратегия 2: незакрытый JSON — дописываем }
    try:
        start = text.index("{")
        fragment = text[start:].rstrip().rstrip(",") + "\n}"
        data = json.loads(fragment)
        return str(data.get("answer", "Нет данных")), float(data.get("confidence", 0.0))
    except Exception:
        pass

    # Стратегия 3: regex по полям
    answer_match = re.search(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
    conf_match   = re.search(r'"confidence"\s*:\s*([0-9.]+)', text)
    if answer_match:
        answer = answer_match.group(1).strip() or "Нет данных"
        confidence = float(conf_match.group(1)) if conf_match else 0.0
        return answer, confidence

    # Стратегия 4: чистый текст без JSON — берём как есть (для summary-режима)
    clean = text.strip()
    return clean if clean else "Нет данных", 0.5


def generate_answer(query: str, context: str) -> RAGAnswer:
    is_summary = _is_summary_request(query)

    if is_summary:
        prompt = f"""Ты помощник, который пересказывает содержимое документа на основе предоставленного контекста.

ПРАВИЛА:
- используй ТОЛЬКО информацию из контекста
- пиши связным текстом, не списком
- если данных недостаточно — напиши что именно есть в документе
- отвечай на русском языке

КОНТЕКСТ:
{context}

ЗАДАНИЕ:
{query}

ОТВЕТ (связный текст):"""

        try:
            r = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3,
                },
                timeout=120,
            )
            r.raise_for_status()
            raw = r.json()["response"].strip()
            return RAGAnswer(answer=raw, confidence=0.85, raw=raw)
        except requests.RequestException as e:
            return RAGAnswer(answer="Ошибка соединения с LLM", confidence=0.0, raw=str(e))

    # Обычный Q&A режим
    prompt = f"""Ты извлекаешь информацию строго из контекста.

ФОРМАТ ОТВЕТА — только JSON, ничего кроме JSON:
{{
  "answer": "...",
  "confidence": 0.0
}}

ПРАВИЛА:
- не выдумывай факты
- если в контексте нет ответа → "Нет данных"
- confidence: число от 0.0 до 1.0
- не добавляй пояснений до или после JSON

КОНТЕКСТ:
{context}

ВОПРОС:
{query}

ОТВЕТ:"""

    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.0,
            },
            timeout=60,
        )
        r.raise_for_status()
        raw = r.json()["response"].strip()
    except requests.RequestException as e:
        return RAGAnswer(answer="Ошибка соединения с LLM", confidence=0.0, raw=str(e))

    answer, confidence = _parse_answer(raw)
    return RAGAnswer(answer=answer, confidence=confidence, raw=raw)