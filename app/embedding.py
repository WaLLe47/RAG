from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "BAAI/bge-m3",
    trust_remote_code=True
)


def get_embedding(text: str):
    if not text:
        return []

    vector = model.encode(
        text,
        normalize_embeddings=True
    )

    return vector.tolist()