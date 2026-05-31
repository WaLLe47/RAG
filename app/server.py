"""
FastAPI сервер для RAG системы.
Запуск: uvicorn app.server:app --reload --port 8000
"""

import sys
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

_APP_DIR = Path(__file__).parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import requests
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ingest import build_index
from qdrant_db import recreate_collection, client, COLLECTION_NAME
from rag import retrieve_chunks, generate_answer
from config import OLLAMA_TAGS_URL, OLLAMA_MODEL

app = FastAPI(title="RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Веб-интерфейс: React-версия из Interface/
_ROOT = Path(__file__).parent.parent
INTERFACE_DIR = _ROOT / "Interface"


# Файлы интерфейса (jsx/css/js) отдаём вручную с запретом кеширования:
# код компилируется в браузере, и закешированная старая версия — частая
# причина «ошибок, которые уже исправлены». no-store заставляет браузер
# всегда брать свежий файл.
_UI_ALLOWED = {".jsx", ".js", ".css", ".html"}


@app.get("/ui/{filename}")
def ui_file(filename: str):
    path = (INTERFACE_DIR / filename).resolve()
    # защита от выхода за пределы папки и от неожиданных типов файлов
    if INTERFACE_DIR not in path.parents or path.suffix.lower() not in _UI_ALLOWED:
        raise HTTPException(404)
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(str(path), headers={"Cache-Control": "no-store"})

# --- состояние ---
_indexed_file: Optional[str] = None
_indexed_chunks: int = 0


@app.on_event("startup")
def _restore_state() -> None:
    """После перезапуска восстанавливаем состояние из Qdrant: если коллекция
    существует и непустая — документ считается загруженным, чтобы /api/ask
    работал без повторной загрузки."""
    global _indexed_file, _indexed_chunks
    try:
        info = client.get_collection(COLLECTION_NAME)
        if info.points_count and info.points_count > 0:
            _indexed_chunks = info.points_count
            _indexed_file = "проиндексированный документ"
            print(f"[server] Восстановлено состояние: {_indexed_chunks} чанков")
    except Exception:
        pass  # коллекции ещё нет — это нормально для первого запуска


# --- схемы ---
class QuestionRequest(BaseModel):
    question: str


class Source(BaseModel):
    id: str
    score: float
    text: str


class QuestionResponse(BaseModel):
    answer: str
    confidence: float
    context: str
    sources: list[Source]


class StatusResponse(BaseModel):
    indexed: bool
    file_name: Optional[str]
    chunks: int


# --- эндпоинты ---

@app.get("/")
def index():
    react_html = INTERFACE_DIR / "RAG Interface.html"
    if react_html.exists():
        return FileResponse(str(react_html), headers={"Cache-Control": "no-store"})
    return {"status": "RAG API running"}


@app.get("/api/health")
def health():
    """Проверяет доступность Qdrant и Ollama (на стороне сервера)."""
    qdrant_ok = True
    try:
        client.get_collections()
    except Exception:
        qdrant_ok = False

    ollama_ok = True
    try:
        r = requests.get(OLLAMA_TAGS_URL, timeout=2)
        ollama_ok = r.ok
    except requests.RequestException:
        ollama_ok = False

    return {"qdrant": qdrant_ok, "ollama": ollama_ok, "model": OLLAMA_MODEL}


@app.get("/api/status", response_model=StatusResponse)
def status():
    return StatusResponse(
        indexed=_indexed_file is not None,
        file_name=Path(_indexed_file).name if _indexed_file else None,
        chunks=_indexed_chunks,
    )


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    global _indexed_file, _indexed_chunks

    allowed = {".pdf", ".docx", ".txt"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(400, f"Формат не поддерживается. Допустимые: {', '.join(allowed)}")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    try:
        shutil.copyfileobj(file.file, tmp)
        tmp.close()

        recreate_collection()
        build_index(tmp.name)

        info = client.get_collection(COLLECTION_NAME)
        _indexed_chunks = info.points_count
        _indexed_file = file.filename

        return {"ok": True, "file": file.filename, "chunks": _indexed_chunks}
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        os.unlink(tmp.name)


@app.post("/api/ask", response_model=QuestionResponse)
def ask(body: QuestionRequest):
    if not _indexed_file:
        raise HTTPException(400, "Сначала загрузите документ")

    q = body.question.strip()
    if not q:
        raise HTTPException(400, "Вопрос не может быть пустым")

    chunks = retrieve_chunks(q)
    ctx = "\n\n".join(chunks)
    result = generate_answer(q, ctx)

    # Чанки отдаём как источники с убывающим score (после reranking порядок
    # уже соответствует релевантности).
    sources = [
        Source(
            id=f"chunk #{i + 1}",
            score=round(max(0.0, 0.95 - i * 0.06), 2),
            text=c,
        )
        for i, c in enumerate(chunks)
    ]

    return QuestionResponse(
        answer=result.answer,
        confidence=result.confidence,
        context=ctx,
        sources=sources,
    )


@app.delete("/api/reset")
def reset():
    global _indexed_file, _indexed_chunks
    recreate_collection()
    _indexed_file = None
    _indexed_chunks = 0
    return {"ok": True}