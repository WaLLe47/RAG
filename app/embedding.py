from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL, EMBED_DEVICE

_model: SentenceTransformer | None = None

MODEL_NAME = EMBEDDING_MODEL


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        # device по умолчанию — cpu: вся VRAM остаётся под LLM (qwen2.5:14b),
        # иначе на картах с 16 ГБ возникает CUDA out of memory.
        _model = SentenceTransformer(MODEL_NAME, trust_remote_code=True, device=EMBED_DEVICE)
    return _model


def get_embedding(text: str) -> list[float]:
    if not text or not text.strip():
        raise ValueError("Empty text")
    return _get_model().encode(text, normalize_embeddings=True).tolist()


def get_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors = _get_model().encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]
