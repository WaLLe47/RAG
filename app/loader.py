from pypdf import PdfReader
import docx


def load_pdf(path: str):
    reader = PdfReader(path)

    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


def load_docx(path: str):
    doc = docx.Document(path)

    return "\n".join(
        p.text for p in doc.paragraphs if p.text
    )


def load_file(path: str):
    if path.endswith(".pdf"):
        return load_pdf(path)

    if path.endswith(".docx"):
        return load_docx(path)

    raise Exception("Unsupported file format")