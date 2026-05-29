def _split_long_paragraph(paragraph: str, chunk_size: int) -> list[str]:
    """Разбивает слишком длинный абзац на части по словам, не превышая chunk_size."""
    pieces: list[str] = []
    current = ""
    for word in paragraph.split():
        if len(current) + len(word) + 1 <= chunk_size:
            current = (current + " " + word).strip()
        else:
            if current:
                pieces.append(current)
            current = word
    if current:
        pieces.append(current)
    return pieces


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    # Абзацы длиннее chunk_size заранее режем на части, иначе они превратятся
    # в один огромный чанк, который плохо ищется и переполняет контекст.
    expanded: list[str] = []
    for p in paragraphs:
        if len(p) > chunk_size:
            expanded.extend(_split_long_paragraph(p, chunk_size))
        else:
            expanded.append(p)
    paragraphs = expanded

    chunks: list[str] = []
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
