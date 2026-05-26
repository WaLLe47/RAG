from embedding import get_embedding
from qdrant_db import client, COLLECTION_NAME


def search(query: str, top_k: int = 10):

    vector = get_embedding(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=top_k,
        with_payload=True
    )

    return [r.payload["text"] for r in results.points]