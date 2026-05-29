import uuid
from loader import load_file
from chunker import chunk_text
from embedding import get_embeddings
from qdrant_db import client, COLLECTION_NAME

BATCH_SIZE = 256



def make_id(text: str, i: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{i}:{text}"))


def build_index(file_path: str) -> None:
    text = load_file(file_path)
    chunks = chunk_text(text)

    if not chunks:
        print(f"[ingest] No chunks extracted from {file_path}")
        return

    vectors = get_embeddings(chunks)

    points = [
        {
            "id": make_id(chunk, i),
            "vector": vec,
            "payload": {
                "text": chunk,
                "source": file_path,
                "chunk_id": i,
            },
        }
        for i, (chunk, vec) in enumerate(zip(chunks, vectors))
    ]

    for start in range(0, len(points), BATCH_SIZE):
        batch = points[start : start + BATCH_SIZE]
        client.upsert(COLLECTION_NAME, batch)
        print(f"[ingest] Upserted {start + len(batch)}/{len(points)} points")

    print(f"[ingest] Done: {len(points)} chunks from {file_path}")