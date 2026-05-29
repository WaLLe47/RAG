import os

from ingest import add_file
from qdrant_db import recreate_collection
from rag import build_context, generate_answer


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOC_PATH = os.path.join(BASE_DIR, "data", "test.docx")


def build_db():
    print("BASE_DIR =", BASE_DIR)
    print("DOC_PATH =", DOC_PATH)
    print("Exists =", os.path.exists(DOC_PATH))

    recreate_collection()

    if os.path.exists(DOC_PATH):
        add_file(DOC_PATH)
    else:
        print("File not found")


def ask(query: str):
    context = build_context(query)

    print("\n=== CONTEXT ===\n")
    print(context)

    answer = generate_answer(query=query, context=context)

    print("\n=== ANSWER ===\n")
    print(answer)


if __name__ == "__main__":
    build_db()

    ask("Кто такая Гончарова?")
    ask("Как начать программировать?")
    ask("О чем говорится в документе?")
    ask("Кто такой Трофимов?")