import os

from qdrant_db import create_collection
from ingest import add_document, add_file
from rag import build_context, generate_answer


# 📍 Корень проекта (D:\RAG)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 📁 путь к файлу
DOC_PATH = os.path.join(BASE_DIR, "data", "test.docx")


def build_db():

    print("BASE_DIR =", BASE_DIR)
    print("DOC_PATH =", DOC_PATH)
    print("Exists =", os.path.exists(DOC_PATH))

    create_collection()


    # 📄 загрузка файла
    if os.path.exists(DOC_PATH):
        add_file(DOC_PATH)
    else:
        print("Файл не найден, пропускаю:", DOC_PATH)


def ask(query: str):

    context = build_context(query)
    answer = generate_answer(query, context)

    print("\n=== ANSWER ===\n")
    print(answer)


if __name__ == "__main__":

    build_db()

    ask("Кто такая Гончарова?")
    ask("Как начать программировать?")
    ask("О чем говориться в документе?")