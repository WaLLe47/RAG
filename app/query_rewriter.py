import requests

from config import OLLAMA_URL, OLLAMA_MODEL

_BAD_RESPONSES = {"нет данных", "no data", "нет", "none", "null", "не знаю", "unknown"}


def rewrite_query(query: str) -> str:
    """
    Переписывает запрос для семантического поиска.
    При любой ошибке или подозрительном ответе возвращает оригинал.
    """
    if len(query.strip()) < 10:
        return query

    prompt = f"""Перепиши запрос для семантического поиска в документе.

Правила:
- сделай его более формальным и конкретным
- убери разговорные слова
- сохрани исходный смысл
- верни ТОЛЬКО переписанный запрос, без пояснений

Запрос: {query}

Переписанный запрос:"""

    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.0,
            },
            timeout=15,
        )
        r.raise_for_status()
        result = r.json()["response"].strip()

        if not result:
            return query
        if result.lower().strip(".").strip() in _BAD_RESPONSES:
            return query
        if len(result) > len(query) * 3:
            return query

        return result
    except requests.RequestException as e:
        print(f"[query_rewriter] Ollama недоступна, используем оригинал: {e}")
        return query