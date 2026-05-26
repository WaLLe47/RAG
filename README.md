# RAG System (BGE-M3 + Qdrant + Ollama)

## 📌 Описание

Минимальная реализация Retrieval-Augmented Generation (RAG) системы:

- Embeddings: BAAI BGE-M3
- Vector DB: Qdrant
- LLM: Ollama (Llama3)
- Поддержка DOCX документов
- Chunking + semantic search

---

## 🧠 Архитектура
Document → Chunking → Embedding → Qdrant → Retrieval → LLM → Answer

---

## ⚙️ Установка

```bash
pip install -r requirements.txt
docker run -p 6333:6333 qdrant/qdrant
ollama run llama3
python app/main.py
```

## 📂 Структура
- app/ — основной код
- data/ — входные документы (игнорируются git)
- embedding.py — модель эмбеддингов
- rag.py — генерация ответа
