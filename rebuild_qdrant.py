"""
Пересборка коллекции stationery_rag в работающий Qdrant-сервер.
Запуск: python rebuild_qdrant.py
Требует: Qdrant-сервер на http://localhost:6333
"""
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from tqdm import tqdm

TEXT_FILE = r"E:\mcp\канцелярия.txt"
COLLECTION = "stationery_rag"
QDRANT_URL = "http://localhost:6333"
MODEL_NAME = "sergeyzh/rubert-mini-sts"
BATCH = 64


def chunk_by_paragraphs(text, min_len=100, max_len=1500):
    """Разбивает текст на чанки по абзацам."""
    text = re.sub(r"\r\n", "\n", text)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks = []
    buffer = ""
    for p in paragraphs:
        if len(p) > max_len:
            sentences = re.split(r"(?<=[.!?])\s+", p)
            for s in sentences:
                if len(buffer) + len(s) + 1 <= max_len:
                    buffer = (buffer + " " + s).strip()
                else:
                    if buffer:
                        chunks.append(buffer)
                    buffer = s
        else:
            if len(buffer) + len(p) + 2 > max_len:
                if buffer:
                    chunks.append(buffer)
                buffer = p
            else:
                buffer = (buffer + "\n\n" + p).strip() if buffer else p

    if buffer:
        chunks.append(buffer)

    return [c for c in chunks if len(c) >= min_len]


def main():
    text_path = Path(TEXT_FILE)
    if not text_path.exists():
        print(f"✗ Файл не найден: {TEXT_FILE}")
        return

    print(f"Читаю {TEXT_FILE}")
    raw = text_path.read_text(encoding="utf-8")
    print(f"Символов: {len(raw):,}")

    chunks = chunk_by_paragraphs(raw)
    print(f"Чанков: {len(chunks)}")

    if not chunks:
        print("✗ Не получилось ни одного чанка. Проверь файл.")
        return

    print(f"Загружаю модель {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    dim = model.get_sentence_embedding_dimension()
    print(f"Размерность: {dim}")

    print("Кодирую вектора...")
    vectors = []
    for i in tqdm(range(0, len(chunks), BATCH), desc="Batches"):
        batch = chunks[i:i + BATCH]
        vecs = model.encode(batch, normalize_embeddings=True, show_progress_bar=False)
        vectors.extend(vecs.tolist())

    print(f"Подключаюсь к {QDRANT_URL}")
    client = QdrantClient(url=QDRANT_URL)

    if client.collection_exists(COLLECTION):
        print(f"Удаляю старую коллекцию {COLLECTION}")
        client.delete_collection(COLLECTION)

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )
    print(f"Создана коллекция {COLLECTION}, dim={dim}, Cosine")

    print("Заливаю точки в Qdrant...")
    points = [
        PointStruct(
            id=i,
            vector=vectors[i],
            payload={
                "text": chunks[i],
                "chunk_id": i,
                "length": len(chunks[i]),
            },
        )
        for i in range(len(chunks))
    ]
    client.upsert(collection_name=COLLECTION, points=points)

    info = client.get_collection(COLLECTION)
    print(f"\n✓ Готово. Points count: {info.points_count}")


if __name__ == "__main__":
    main()