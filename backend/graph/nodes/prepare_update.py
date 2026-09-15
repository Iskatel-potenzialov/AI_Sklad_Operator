"""
Узел: prepare_update
Готовит изменение min_stock: показывает "было → станет" и ждёт подтверждения.
"""
from langgraph.types import interrupt
from backend.graph.state import GraphState


def _find_item(state: GraphState) -> dict | None:
    """Ищет целевой товар в state.items."""
    if not state.target_item_id:
        return None
    for item in state.items:
        if item.get("item_id") == state.target_item_id:
            return item
    return None


def _build_proposal(item: dict, new_value: int) -> dict:
    """Собирает proposal для interrupt()."""
    old_value = item.get("min_stock", 0)
    return {
        "action_type": "update_min_stock",
        "target_item_id": item.get("item_id"),
        "product_name": item.get("product_name", ""),
        "field": "min_stock",
        "old_value": old_value,
        "new_value": new_value,
        "description": (
            f"Изменить минимальный остаток товара "
            f"«{item.get('product_name', '?')}» ({item.get('item_id')}) "
            f"с {old_value} на {new_value}"
        ),
    }


def prepare_update(state: GraphState) -> dict:
    """
    Узел: prepare_update.
    Формирует proposal, вызывает interrupt() и ждёт подтверждения.
    """
    print(f"[prepare_update] Preparing update for run {state.run_id}")

    # 1. Валидация: указан ли товар
    item = _find_item(state)
    if not item:
        return {
            "answer": f"Товар {state.target_item_id} не найден.",
            "errors": state.errors + [f"Item {state.target_item_id} not found"],
            "route_trace": state.route_trace + ["prepare_update: item not found"],
        }

    # 2. Валидация: указано ли новое значение
    if state.new_min_stock is None:
        return {
            "answer": "Не указано новое значение min_stock. Пример: «Поменяй min_stock у item_012 на 50».",
            "route_trace": state.route_trace + ["prepare_update: no new_min_stock"],
        }

    if state.new_min_stock < 0:
        return {
            "answer": f"Некорректное значение: {state.new_min_stock}. Должно быть ≥ 0.",
            "route_trace": state.route_trace + ["prepare_update: negative value"],
        }

    # 3. Собираем proposal
    proposal = _build_proposal(item, state.new_min_stock)
    print(f"[prepare_update] Proposal: {proposal}")

    # 4. HITL — ждём подтверждения
    human_response = interrupt({"pending_action": proposal})
    print(f"[prepare_update] Human response: {human_response}")

    approved = isinstance(human_response, dict) and bool(human_response.get("approved"))

    return {
        "action_approved": approved,
        "pending_action": proposal,
        "route_trace": state.route_trace + [
            f"prepare_update: {'approved' if approved else 'rejected'}"
        ],
    }