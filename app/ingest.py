import hashlib
import re
from loader import load_file
from embedding import get_embedding
from qdrant_db import client, COLLECTION_NAME


def normalize(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)

    return text.strip()

def chunk_text(
    text: str,
    chunk_size: int = 700,
    overlap: int = 120
):
    paragraphs = [
        p.strip()
        for p in text.split("\n")
        if p.strip()
    ]

    chunks = []
    current = ""

    for p in paragraphs:

        if len(current) + len(p) <= chunk_size:
            current += "\n" + p

        else:
            chunks.append(current.strip())

            tail = current[-overlap:]

            current = tail + "\n" + p

    if current.strip():
        chunks.append(current.strip())

    return chunks

def make_id(source: str, chunk_id: int, text: str) -> str:
    raw = f"{source}:{chunk_id}:{text}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def add_file(file_path: str):
    text = normalize(load_file(file_path))
    chunks = chunk_text(text)

    points = []

    for i, chunk in enumerate(chunks):
        vector = get_embedding(chunk)

        points.append({
            "id": make_id(file_path, i, chunk),
            "vector": vector,
            "payload": {
                "text": chunk,
                "source": file_path,
                "chunk_id": i
            }
        })

    if not points:
        print("No chunks to insert")
        return

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    print(f"Inserted/updated {len(points)} chunks from {file_path}")