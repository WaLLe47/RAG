from pypdf import PdfReader
import docx


def load_pdf(path: str) -> str:
    """
    Чтение PDF файла
    """
    reader = PdfReader(path)
    text = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)

    return "\n".join(text)


def load_docx(path: str) -> str:
    """
    Чтение DOCX файла
    """
    doc = docx.Document(path)

    text = []

    for para in doc.paragraphs:
        if para.text.strip():
            text.append(para.text)

    return "\n".join(text)


def load_file(path: str) -> str:
    """
    Универсальная загрузка
    """

    if path.endswith(".pdf"):
        return load_pdf(path)

    if path.endswith(".docx"):
        return load_docx(path)

    raise ValueError("Unsupported file format: " + path)