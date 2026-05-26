import re

def split_text(text: str, chunk_size: int = 400, overlap: int = 80):

    text = re.sub(r"\s+", " ", text).strip()

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks