from embedding import get_embedding
from qdrant_db import client, COLLECTION_NAME
from bm25 import BM25Index

_bm25_index: BM25Index | None = None


def vector_search(query: str, top_k: int = 20) -> list[str]:
    vector = get_embedding(query)
    res = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=top_k,
        with_payload=True,
    )
    return [p.payload["text"] for p in res.points]


def _reciprocal_rank_fusion(
    *rankings: list[str], k: int = 60
) -> list[str]:
    """Объединяет несколько ранжированных списков через RRF."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=lambda d: scores[d], reverse=True)


def hybrid_search(query: str, all_chunks: list[str], top_k: int = 20) -> list[str]:
    """Гибридный поиск: vector + BM25 с RRF fusion."""
    global _bm25_index

    if _bm25_index is None or _bm25_index.chunks != all_chunks:
        _bm25_index = BM25Index(all_chunks)

    vec_results = vector_search(query, top_k=top_k)
    bm25_results = _bm25_index.search(query, top_k=top_k)

    return _reciprocal_rank_fusion(vec_results, bm25_results)[:top_k]