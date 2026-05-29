import re

from rank_bm25 import BM25Okapi

# \w в Python по умолчанию работает в Unicode-режиме, поэтому корректно
# токенизирует и кириллицу, отбрасывая пунктуацию.
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class BM25Index:
    def __init__(self, chunks: list[str]):
        self.chunks = chunks
        tokenized = [_tokenize(c) for c in chunks]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query: str, top_k: int = 10) -> list[str]:
        scores = self.bm25.get_scores(_tokenize(query))
        ranked = sorted(zip(self.chunks, scores), key=lambda x: x[1], reverse=True)
        return [c for c, _ in ranked[:top_k]]
