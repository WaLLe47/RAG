from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

from config import QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME, VECTOR_SIZE

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


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
