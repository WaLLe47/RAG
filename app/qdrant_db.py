from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

from embedding import model

COLLECTION_NAME = "documents"

client = QdrantClient(
    host="localhost",
    port=6333
)


def create_collection():
    collections = client.get_collections().collections
    names = [c.name for c in collections]

    vector_size = model.get_embedding_dimension()

    if COLLECTION_NAME not in names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        print("Collection created")
    else:
        print("Collection already exists")


def recreate_collection():

    collections = client.get_collections().collections
    names = [c.name for c in collections]

    if COLLECTION_NAME in names:
        client.delete_collection(COLLECTION_NAME)

    create_collection()

    print("Collection recreated")