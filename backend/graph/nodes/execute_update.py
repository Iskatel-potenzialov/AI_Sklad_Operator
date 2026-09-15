"""
Узел: execute_update
Выполняет изменение min_stock после подтверждения (HITL).
"""
from backend.graph.state import GraphState
from backend.mcp_client.client import get_mcp_client


def execute_update(state: GraphState) -> dict:
    """
    Узел: execute_update.
    Вызывает MCP-инструмент update_min_stock для изменения Excel.
    """
    print(f"[execute_update] Executing update for run {state.run_id}")

    # 1. Проверка: подтверждено ли
    if not state.action_approved:
        print(f"[execute_update] Action not approved, skipping")
        return {
            "answer": "❌ Изменение отменено пользователем.",
            "route_trace": state.route_trace + ["execute_update: rejected"],
        }

    # 2. Проверка proposal
    proposal = state.pending_action or {}
    if proposal.get("action_type") != "update_min_stock":
        return {
            "answer": "Ошибка: нет действия для выполнения.",
            "errors": state.errors + ["execute_update: no valid pending_action"],
            "route_trace": state.route_trace + ["execute_update: no action"],
        }

    item_id = proposal.get("target_item_id")
    new_value = proposal.get("new_value")
    old_value = proposal.get("old_value")

    print(f"[execute_update] {item_id}: {old_value} → {new_value}")

    # 3. Вызов MCP
    mcp_client = get_mcp_client()
    result = mcp_client.update_min_stock(item_id=item_id, new_min_stock=new_value)

    if result.get("success"):
        print(f"[execute_update] ✓ Updated {item_id}: {old_value} → {new_value}")
        return {
            "answer": (
                f"✅ Минимальный остаток товара «{proposal.get('product_name')}» "
                f"({item_id}) изменён: {old_value} → {new_value}."
            ),
            "route_trace": state.route_trace + [
                f"execute_update: {item_id} {old_value} → {new_value}"
            ],
        }

    error_msg = result.get("error", "Неизвестная ошибка")
    error_code = result.get("error_code", "UNKNOWN_ERROR")
    print(f"[execute_update] ✗ Failed: {error_msg}")
    return {
        "answer": f"✗ Не удалось изменить остаток {item_id}: {error_msg}",
        "errors": state.errors + [f"MCP error ({error_code}): {error_msg}"],
        "route_trace": state.route_trace + ["execute_update: failed"],
    }