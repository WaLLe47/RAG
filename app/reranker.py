from sentence_transformers import CrossEncoder

from config import RERANKER_MODEL

_model: CrossEncoder | None = None
MODEL_NAME = RERANKER_MODEL


def _get_model() -> CrossEncoder:
    global _model
    if _model is None:
        _model = CrossEncoder(MODEL_NAME)
    return _model


def rerank(query: str, chunks: list[str], top_k: int = 5) -> list[str]:
    if not chunks:
        return []

    model = _get_model()
    pairs = [(query, c) for c in chunks]
    scores = model.predict(pairs)

    ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
    return [c for c, _ in ranked[:top_k]]
