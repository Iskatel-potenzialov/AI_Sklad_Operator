"""
Детерминированные метрики retrieval: Precision@k, Recall@k, MRR.
Без LLM, без токенов, мгновенно.
"""


def precision_at_k(expected: list[int], retrieved: list[int], k: int = 5) -> float:
    """Доля релевантных в топ-k от размера топ-k."""
    if not retrieved:
        return 0.0
    top = retrieved[:k]
    hits = sum(1 for cid in top if cid in expected)
    return hits / len(top)


def recall_at_k(expected: list[int], retrieved: list[int], k: int = 5) -> float:
    """Доля эталонных чанков, которые попали в топ-k."""
    if not expected:
        return 0.0
    top = retrieved[:k]
    hits = sum(1 for cid in expected if cid in top)
    return hits / len(expected)


def mrr(expected: list[int], retrieved: list[int]) -> float:
    """Mean Reciprocal Rank — 1/позиция первого правильного чанка."""
    for i, cid in enumerate(retrieved, 1):
        if cid in expected:
            return 1.0 / i
    return 0.0


def hit_at_k(expected: list[int], retrieved: list[int], k: int = 5) -> float:
    """Есть ли хоть один правильный в топ-k."""
    return 1.0 if any(cid in expected for cid in retrieved[:k]) else 0.0


def compute_all(expected: list[int], retrieved: list[int], k: int = 5) -> dict:
    """Возвращает все метрики одним словарём."""
    return {
        f"precision@{k}": round(precision_at_k(expected, retrieved, k), 3),
        f"recall@{k}": round(recall_at_k(expected, retrieved, k), 3),
        f"hit@{k}": hit_at_k(expected, retrieved, k),
        "mrr": round(mrr(expected, retrieved), 3),
        "expected_count": len(expected),
        "retrieved_count": len(retrieved),
    }