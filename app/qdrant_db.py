from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from embedding import VECTOR_SIZE

COLLECTION_NAME = "documents"

client = QdrantClient(host="localhost", port=6333)


def recreate_collection() -> None:
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )