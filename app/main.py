import sys
import argparse
from pathlib import Path

from ingest import build_index
from qdrant_db import recreate_collection
from rag import build_context, generate_answer


def build_db(doc_path: str) -> None:
    print(f"[main] Создаём коллекцию и индексируем: {doc_path}")
    recreate_collection()
    build_index(doc_path)
    print("[main] Индексирование завершено")


def ask(question: str) -> None:
    print(f"\n>>> {question}")

    ctx = build_context(question)
    print("\n=== CONTEXT ===")
    print(ctx)

    result = generate_answer(question, ctx)
    print("\n=== ANSWER ===")
    print(f"Ответ:      {result.answer}")
    print(f"Confidence: {result.confidence:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG pipeline")
    parser.add_argument(
        "--doc",
        type=str,
        default=None,
        help="Путь к документу для индексирования (PDF/DOCX/TXT)",
    )
    parser.add_argument(
        "--query",
        type=str,
        nargs="+",
        default=["О чём документ?", "Кто такой Трофимов?", "Кто такая Гончарова?", "Как начать програмировать", "Кто подал заявление?" ],
        help="Один или несколько вопросов",
    )
    parser.add_argument(
        "--skip-index",
        action="store_true",
        help="Не переиндексировать, использовать существующую коллекцию",
    )
    args = parser.parse_args()

    if not args.skip_index:
        if args.doc is None:
            default = Path(__file__).parent.parent / "data" / "test.docx"
            doc_path = str(default)
        else:
            doc_path = args.doc

        if not Path(doc_path).exists():
            print(f"[main] Файл не найден: {doc_path}")
            sys.exit(1)

        build_db(doc_path)

    for q in args.query:
        ask(q)


if __name__ == "__main__":
    main()