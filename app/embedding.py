from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None

MODEL_NAME = "BAAI/bge-m3"
VECTOR_SIZE = 1024


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
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