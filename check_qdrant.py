from qdrant_client import QdrantClient
import json

client = QdrantClient(url="http://localhost:6333")

collections = client.get_collections()
print("Collections:")
for c in collections.collections:
    print(f"  - {c.name}")

for c in collections.collections:
    info = client.get_collection(c.name)
    print(f"\n=== {c.name} ===")
    print(f"  Points count: {info.points_count}")
    vectors_config = info.config.params.vectors
    if hasattr(vectors_config, "size"):
        print(f"  Vector dim: {vectors_config.size}")
        print(f"  Distance: {vectors_config.distance}")

if collections.collections:
    name = collections.collections[0].name
    points, _ = client.scroll(
        collection_name=name,
        limit=2,
        with_payload=True,
        with_vectors=False,
    )
    print(f"\n=== Sample payloads from {name} ===")
    for i, p in enumerate(points, 1):
        print(f"\n[{i}] id={p.id}")
        print(json.dumps(p.payload, ensure_ascii=False, indent=2))