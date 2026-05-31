"""
Централизованная конфигурация.
Все сетевые адреса и имена моделей читаются из переменных окружения
(с разумными значениями по умолчанию), что позволяет запускать проект
локально и в Docker без правки исходного кода.
"""

import os

try:
    from dotenv import load_dotenv

    load_dotenv()  # подхватывает .env из корня проекта, если он есть
except ImportError:
    # python-dotenv не обязателен — без него просто используются os.environ
    pass


# --- Qdrant ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "documents")

# --- Ollama (LLM) ---
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_TAGS_URL = os.getenv("OLLAMA_TAGS_URL", "http://localhost:11434/api/tags")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")

# --- Модели ---
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", "1024"))
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")

# Устройство для эмбеддингов/реранкера. "cpu" по умолчанию, чтобы вся VRAM
# доставалась LLM (на 16 ГБ qwen2.5:14b + модели на GPU не помещаются).
# Поставьте EMBED_DEVICE=cuda, если у вас карта с большим объёмом памяти.
EMBED_DEVICE = os.getenv("EMBED_DEVICE", "cpu")
