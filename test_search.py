"""Быстрый тест поиска по базе знаний."""
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

MODEL_NAME = "sergeyzh/rubert-mini-sts"
COLLECTION = "stationery_rag"
QDRANT_URL = "http://localhost:6333"

print("Загружаю модель...")
model = SentenceTransformer(MODEL_NAME)
client = QdrantClient(url=QDRANT_URL)

queries = [
    "Требования к хранению бумаги",
    "Температура и влажность на складе",
    "Ширина проездов в складе",
    "Высота складских помещений",
]

for q in queries:
    print(f"\n{'=' * 70}")
    print(f"🔎 {q}")
    print('=' * 70)

    vec = model.encode(q, normalize_embeddings=True).tolist()
    hits = client.query_points(
        collection_name=COLLECTION,
        query=vec,
        limit=3,
    ).points

    for i, h in enumerate(hits, 1):
        text = h.payload["text"][:300].replace("\n", " ")
        print(f"\n[{i}] score={h.score:.4f}")
        print(f"    {text}...")