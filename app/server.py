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

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ingest import build_index
from qdrant_db import recreate_collection, client, COLLECTION_NAME
from rag import build_context, generate_answer

app = FastAPI(title="RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статика (index.html)
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# --- состояние ---
_indexed_file: Optional[str] = None
_indexed_chunks: int = 0


# --- схемы ---
class QuestionRequest(BaseModel):
    question: str


class QuestionResponse(BaseModel):
    answer: str
    confidence: float
    context: str


class StatusResponse(BaseModel):
    indexed: bool
    file_name: Optional[str]
    chunks: int


# --- эндпоинты ---

@app.get("/")
def index():
    html = STATIC_DIR / "index.html"
    if html.exists():
        return FileResponse(str(html))
    return {"status": "RAG API running"}


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

    ctx = build_context(q)
    result = generate_answer(q, ctx)

    return QuestionResponse(
        answer=result.answer,
        confidence=result.confidence,
        context=ctx,
    )


@app.delete("/api/reset")
def reset():
    global _indexed_file, _indexed_chunks
    recreate_collection()
    _indexed_file = None
    _indexed_chunks = 0
    return {"ok": True}