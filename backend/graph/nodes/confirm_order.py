"""
Узел: confirm_order
Формирует предложение заказа, ждёт подтверждения и записывает заказ в SQLite.
"""
from datetime import datetime
from langgraph.types import interrupt
from backend.graph.state import GraphState
from backend.db import save_order, mark_telegram_sent
from backend.mcp.telegram import send_telegram_message, format_order_message


def _find_supplier(state: GraphState) -> dict | None:
    """Ищет данные поставщика в state.suppliers."""
    for supplier in state.suppliers:
        if supplier.get("supplier_id") == state.target_supplier_id:
            return supplier
    return None


def _build_proposal(state: GraphState, supplier_data: dict) -> dict:
    """Собирает proposal для interrupt()."""
    return {
        "action_type": "create_order",
        "supplier_id": state.target_supplier_id,
        "supplier_name": supplier_data.get("company_name", "Неизвестно"),
        "items": state.items_to_order,
        "total_cost": state.total_cost,
        "description": (
            f"Заказ товаров у поставщика {supplier_data.get('company_name')} "
            f"на сумму {state.total_cost:.2f} руб."
        ),
    }


async def _send_telegram_notification(
    supplier_name: str, items: list, total_cost: float
) -> bool:
    """Отправляет уведомление в Telegram. Возвращает True при успехе."""
    try:
        message = format_order_message(
            supplier_name=supplier_name,
            items=items,
            total_cost=total_cost,
        )
        await send_telegram_message(message=message)
        return True
    except Exception as e:
        print(f"[confirm_order] ⚠ Telegram error: {e}")
        return False


async def _handle_approved(state: GraphState, proposal: dict) -> dict:
    """Пользователь подтвердил — пишем заказ в БД и шлём в Telegram."""
    order_data = {
        "run_id": state.run_id,
        "timestamp": datetime.now().isoformat(),
        "supplier_id": state.target_supplier_id,
        "supplier_name": proposal.get("supplier_name"),
        "items": state.items_to_order,
        "total_cost": state.total_cost,
        "status": "confirmed",
    }

    # 1. Пишем в БД. save_order защищает от дублей по run_id.
    saved = await save_order(order_data)
    if not saved:
        return {
            "answer": "⚠️ Заказ уже был подтверждён ранее (дубликат).",
            "order_confirmation": order_data,
            "action_approved": True,
            "pending_action": proposal,
            "route_trace": state.route_trace + ["confirm_order: duplicate ignored"],
        }
    print(f"[confirm_order] ✓ Order saved to DB (run_id={state.run_id})")

    # 2. Telegram — не критично, если упадёт
    telegram_sent = await _send_telegram_notification(
        supplier_name=proposal.get("supplier_name", "Unknown"),
        items=state.items_to_order,
        total_cost=state.total_cost,
    )
    if telegram_sent:
        await mark_telegram_sent(state.run_id)
        print(f"[confirm_order] ✓ Telegram notification sent")

    parts = [
        "✅ Заказ подтверждён и записан в БД.",
        "",
        f"Поставщик: {proposal.get('supplier_name')} ({state.target_supplier_id})",
        f"Товары: {len(state.items_to_order)} позиций",
        f"Сумма: {state.total_cost:.2f} руб.",
        f"Время: {order_data['timestamp']}",
    ]
    parts.append("📱 Уведомление отправлено в Telegram" if telegram_sent
                 else "⚠️ Не удалось отправить уведомление в Telegram")

    return {
        "answer": "\n".join(parts),
        "order_confirmation": order_data,
        "action_approved": True,
        "pending_action": proposal,
        "route_trace": state.route_trace + ["confirm_order: approved and saved"],
    }


def _handle_rejected(proposal: dict) -> dict:
    """Пользователь отклонил заказ."""
    print(f"[confirm_order] Order rejected by user")
    return {
        "answer": "❌ Заказ отклонён пользователем.",
        "action_approved": False,
        "pending_action": proposal,
        "route_trace": ["confirm_order: rejected"],
    }


async def confirm_order(state: GraphState) -> dict:
    """
    Узел: confirm_order.
    Формирует proposal, ждёт interrupt, по результату — записывает заказ или отклоняет.
    """
    print(f"[confirm_order] Preparing order confirmation for supplier {state.target_supplier_id}")

    supplier_data = _find_supplier(state)
    if not supplier_data:
        return {
            "answer": f"Поставщик {state.target_supplier_id} не найден.",
            "errors": state.errors + [f"Supplier {state.target_supplier_id} not found"],
            "route_trace": state.route_trace + ["confirm_order: supplier not found"],
        }

    proposal = _build_proposal(state, supplier_data)
    print(f"[confirm_order] Proposal: {proposal}")

    # Стоп-точка: ждём подтверждения пользователя.
    human_response = interrupt({"pending_action": proposal})
    print(f"[confirm_order] Human response: {human_response}")

    if isinstance(human_response, dict) and human_response.get("approved"):
        return await _handle_approved(state, proposal)
    else:
        return _handle_rejected(proposal)