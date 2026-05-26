from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "BAAI/bge-m3",
    device="cpu"
)

def get_embedding(text: str):
    return model.encode(text, normalize_embeddings=True).tolist()