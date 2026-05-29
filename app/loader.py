from pypdf import PdfReader
import docx


def load_pdf(path: str) -> str:
    text = ""
    reader = PdfReader(path)
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    return text


def load_docx(path: str) -> str:
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text)


def load_txt(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


LOADERS = {
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".txt": load_txt,
}


def load_file(path: str) -> str:
    for ext, loader in LOADERS.items():
        if path.lower().endswith(ext):
            return loader(path)
    supported = ", ".join(LOADERS.keys())
    raise ValueError(f"Unsupported format. Supported: {supported}")