from embedding import get_embedding
from qdrant_db import client, COLLECTION_NAME


def search(
    query: str,
    top_k: int = 10,
    score_threshold: float = 0.25
):

    vector = get_embedding(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=top_k,
        with_payload=True
    )

    chunks = []

    for r in results.points:

        if r.score < score_threshold:
            continue

        text = r.payload.get("text", "").strip()

        if len(text) > 20:
            chunks.append(text)

    return chunks