"""
RAG-сервис: превращает текст в вектор через rubert-mini-sts.
Запуск: python -m uvicorn rag_service.server:app --port 8002 --reload
"""
import os
os.environ.setdefault("HF_HOME", r"E:\mcp\models\huggingface")

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer


MODEL_NAME = "sergeyzh/rubert-mini-sts"
_model: SentenceTransformer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model
    print(f"[rag_service] Loading model {MODEL_NAME}...")
    _model = SentenceTransformer(MODEL_NAME)
    dim = _model.get_sentence_embedding_dimension()
    print(f"[rag_service] Model loaded, dim={dim}")
    yield
    print("[rag_service] Shutting down")


app = FastAPI(title="RAG Embeddings Service", version="0.1.0", lifespan=lifespan)


class EmbedRequest(BaseModel):
    text: str


class EmbedResponse(BaseModel):
    vector: list[float]
    dim: int


class EmbedBatchRequest(BaseModel):
    texts: list[str]


class EmbedBatchResponse(BaseModel):
    vectors: list[list[float]]
    dim: int


@app.post("/embed", response_model=EmbedResponse)
async def embed(req: EmbedRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    vec = _model.encode(req.text, normalize_embeddings=True)
    return EmbedResponse(vector=vec.tolist(), dim=len(vec))


@app.post("/embed_batch", response_model=EmbedBatchResponse)
async def embed_batch(req: EmbedBatchRequest):
    if not req.texts:
        raise HTTPException(status_code=400, detail="Texts list is empty")
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    vecs = _model.encode(req.texts, normalize_embeddings=True, show_progress_bar=False)
    return EmbedBatchResponse(vectors=vecs.tolist(), dim=len(vecs[0]))


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": _model is not None}