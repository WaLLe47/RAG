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


# Маленькие документы целиком влезают в контекст модели — тогда retrieval
# не нужен, отдаём весь текст в исходном порядке (надёжнее для «собирающих»
# вопросов: перечисли всех авторов, все почты, все задачи и т.п.).
_FULL_DOC_CHAR_LIMIT = 24000

# Вопросы-перечисления: ответ собирается из многих мест документа.
_LISTING_KEYWORDS = (
    "все", "всех", "всем", "перечисли", "список", "сколько",
    "каждого", "каждой", "авторов", "почты", "почту", "e-mail", "email",
    "задач", "задачи", "задаче", "вопрос",
)


def _get_all_chunks() -> list[str]:
    """Все чанки в ИСХОДНОМ порядке документа (сортировка по chunk_id)."""
    points = []
    offset = None
    while True:
        resp = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=256,
            offset=offset,
            with_payload=True,
        )
        batch, next_offset = resp
        points.extend(batch)
        if next_offset is None:
            break
        offset = next_offset

    # Восстанавливаем порядок документа — scroll возвращает в произвольном.
    points.sort(key=lambda p: p.payload.get("chunk_id", 0))
    return [p.payload["text"] for p in points]


def _is_summary_request(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in _SUMMARY_KEYWORDS)


def _is_listing_request(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in _LISTING_KEYWORDS)


def _dedup_clean(chunks: list[str]) -> list[str]:
    seen: set[str] = set()
    cleaned: list[str] = []
    for t in chunks:
        t = " ".join(t.split())
        if len(t) > 30 and t not in seen:
            seen.add(t)
            cleaned.append(t)
    return cleaned


def retrieve_chunks(query: str, use_hybrid: bool = True) -> list[str]:
    """Возвращает список релевантных чанков (без склейки в строку)."""
    all_chunks = _get_all_chunks()
    total_chars = sum(len(c) for c in all_chunks)

    summary = _is_summary_request(query)
    listing = _is_listing_request(query)

    # Если документ небольшой ИЛИ это обзорный/собирающий вопрос — отдаём весь
    # документ в исходном порядке. Это решает «перечисли всех авторов / все
    # почты / условие задачи N»: модель видит ВЕСЬ текст, ничего не теряется.
    if total_chars <= _FULL_DOC_CHAR_LIMIT or summary or listing:
        if total_chars <= _FULL_DOC_CHAR_LIMIT:
            return _dedup_clean(all_chunks)
        # Документ большой, но вопрос собирающий — берём максимум релевантного.
        rewritten = rewrite_query(query)
        chunks = hybrid_search(rewritten, all_chunks, top_k=40)
        top = rerank(rewritten, chunks, top_k=24)
        return _dedup_clean(top)

    # Обычный точечный вопрос по большому документу — узкий retrieval.
    rewritten = rewrite_query(query)
    print(f"[rag] rewritten: {rewritten!r}")
    chunks = hybrid_search(rewritten, all_chunks, top_k=25) if use_hybrid \
        else vector_search(rewritten, top_k=25)
    top = rerank(rewritten, chunks, top_k=10)
    return _dedup_clean(top)


def build_context(query: str, use_hybrid: bool = True) -> str:
    return "\n\n".join(retrieve_chunks(query, use_hybrid))


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
                    "keep_alive": "30m",
                    # num_ctx критичен: по умолчанию Ollama режет контекст до
                    # 4096 токенов, и часть документа теряется → «ответ невпопад».
                    "options": {"temperature": 0.3, "num_predict": 700, "num_ctx": 16384},
                },
                timeout=90,
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
                "keep_alive": "30m",
                # temperature должен быть внутри options, иначе Ollama его игнорирует.
                # num_ctx — чтобы влезал весь переданный контекст (см. summary-режим).
                "options": {"temperature": 0.0, "num_predict": 700, "num_ctx": 16384},
            },
            timeout=90,
        )
        r.raise_for_status()
        raw = r.json()["response"].strip()
    except requests.RequestException as e:
        return RAGAnswer(answer="Ошибка соединения с LLM", confidence=0.0, raw=str(e))

    answer, confidence = _parse_answer(raw)
    return RAGAnswer(answer=answer, confidence=confidence, raw=raw)