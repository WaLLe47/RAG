# RAG System (BGE-M3 + Qdrant + Ollama)

## 📌 Описание

Retrieval-Augmented Generation (RAG) система с гибридным поиском:

- **Embeddings:** BAAI/bge-m3
- **Vector DB:** Qdrant
- **LLM:** Ollama (по умолчанию `qwen2.5:14b`)
- **Reranker:** BAAI/bge-reranker-base (cross-encoder)
- **Гибридный поиск:** векторный + BM25 с объединением через Reciprocal Rank Fusion
- **Переписывание запроса** (query rewriting) перед поиском
- **Форматы документов:** PDF, DOCX, TXT
- **Веб-интерфейс:** React (загрузка документа, чат, источники, статистика)

---

## 🧠 Конвейер (pipeline)

```
Document → Loader → Chunking → Embedding → Qdrant
Query → Rewrite → (Vector search + BM25) → RRF → Rerank → LLM → Answer
```

---

## ⚙️ Требования

- Python **3.11–3.12** (рекомендуется: для `torch`/`sentence-transformers` есть готовые wheels)
- Запущенный **Qdrant** (по умолчанию `localhost:6333`)
- Запущенный **Ollama** с загруженной моделью (по умолчанию `qwen2.5:14b`)

## 🚀 Установка и запуск

```bash
# 1. Зависимости
pip install -r requirements.txt

# 2. Qdrant (Docker)
docker run -p 6333:6333 qdrant/qdrant

# 3. Ollama
ollama pull qwen2.5:14b
# ollama serve  # если сервис ещё не запущен

# 4. (опционально) свои настройки
cp .env.example .env   # отредактируйте при необходимости

# 5. Запуск веб-сервера
uvicorn app.server:app --reload --port 8000
```

Откройте http://localhost:8000 — загрузите документ и задавайте вопросы.

> При первом запуске модели эмбеддингов и реранкера (~несколько ГБ)
> будут скачаны с Hugging Face — это может занять время.

---

## 🔧 Конфигурация

Все параметры можно переопределить через переменные окружения или файл `.env`
(см. `.env.example`): адрес Qdrant, URL и имя модели Ollama, имена моделей
эмбеддингов/реранкера. Без `.env` используются значения по умолчанию.

---

## 📂 Структура

```
app/
  config.py          — конфигурация (env переменные)
  server.py          — FastAPI сервер и REST API
  loader.py          — чтение PDF/DOCX/TXT
  chunker.py         — разбиение текста на чанки
  embedding.py       — модель эмбеддингов (BGE-M3)
  qdrant_db.py       — клиент и коллекция Qdrant
  ingest.py          — индексирование документа
  bm25.py            — BM25-индекс (лексический поиск)
  search.py          — гибридный поиск + RRF
  reranker.py        — cross-encoder переранжирование
  query_rewriter.py  — переписывание запроса через LLM
  rag.py             — сборка контекста и генерация ответа
Interface/           — React веб-интерфейс (HTML + JSX + CSS)
data/                — входные документы
```

## 🌐 REST API

| Метод  | Путь            | Назначение                          |
|--------|-----------------|-------------------------------------|
| GET    | `/`             | веб-интерфейс                        |
| GET    | `/api/status`   | статус индексации                    |
| POST   | `/api/upload`   | загрузка и индексирование документа  |
| POST   | `/api/ask`      | вопрос по документу                  |
| DELETE | `/api/reset`    | очистка коллекции                    |
