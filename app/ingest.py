from uuid import uuid4
from embedding import get_embedding
from qdrant_db import client, COLLECTION_NAME
from chunking import split_text
from loader import load_file


def add_document(text: str, source: str = "manual"):

    chunks = split_text(text)

    points = []

    for i, chunk in enumerate(chunks):

        points.append({
            "id": str(uuid4()),
            "vector": get_embedding(chunk),
            "payload": {
                "text": chunk,
                "source": source,
                "chunk_id": i
            }
        })

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    print(f"Inserted {len(points)} chunks from {source}")


def add_file(path: str):

    text = load_file(path)

    source = path.split("/")[-1]

    add_document(text, source=source)