# dump_chunks.py — запускать в rag_venv
import json
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")
points, _ = client.scroll(
    collection_name="stationery_rag",
    limit=200,
    with_payload=True,
    with_vectors=False,
)

with open("chunks_dump.txt", "w", encoding="utf-8") as f:
    for p in sorted(points, key=lambda x: x.payload["chunk_id"]):
        cid = p.payload["chunk_id"]
        text = p.payload["text"]
        f.write(f"=== CHUNK {cid} ===\n{text}\n\n")

print(f"Готово: {len(points)} чанков → chunks_dump.txt")