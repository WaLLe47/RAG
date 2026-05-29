def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    chunks = []
    current = ""

    for p in paragraphs:
        if len(current) + len(p) + 1 <= chunk_size:
            current = (current + "\n" + p).strip()
        else:
            if current:
                chunks.append(current)
            overlap_text = chunks[-1][-overlap:] if chunks else ""
            current = (overlap_text + "\n" + p).strip()

    if current:
        chunks.append(current)

    return chunks