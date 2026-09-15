"""
Узел: check_order_conditions
Проверяет условия договора поставщика перед заказом.

Числа (сумма заказа, минимальный порог) считает Python.
LLM получает готовые значения и только пишет текстовую рекомендацию.
"""
import re
from langchain_core.messages import HumanMessage, SystemMessage
from backend.graph.state import GraphState
from backend.graph.nodes.utils import get_llm


def _parse_min_order_amount(contract_text: str) -> float | None:
    """
    Достаёт минимальную сумму заказа из contract.txt.
    Ищет паттерн вида "Минимальная сумма заказа: 5000 руб.".
    Возвращает float или None.
    """
    if not contract_text:
        return None

    patterns = [
        r"минимальн\w*\s+сумм\w*[^\d]{0,30}(\d[\d\s]*)\s*(?:руб|₽|rub)",
        r"минимальн\w*\s+заказ\w*[^\d]{0,30}(\d[\d\s]*)\s*(?:руб|₽|rub)",
    ]
    for pat in patterns:
        m = re.search(pat, contract_text, re.IGNORECASE)
        if m:
            num_str = m.group(1).replace(" ", "").replace("\u00a0", "")
            try:
                return float(num_str)
            except ValueError:
                continue
    return None


def _get_item_status(state: GraphState) -> str | None:
    """
    Возвращает строку статуса конкретного товара (если указан target_item_id).
    """
    if not state.target_item_id:
        return None

    from backend.mcp_client.client import get_mcp_client
    mcp_client = get_mcp_client()

    print(f"[check_order_conditions] Loading item: {state.target_item_id}")
    result = mcp_client.get_item(state.target_item_id)

    if not result.get("success"):
        print(f"[check_order_conditions] Item not found: {state.target_item_id}")
        return f"Товар {state.target_item_id} не найден"

    item = result.get("item") or {}
    quantity = item.get("quantity", 0)
    min_stock = item.get("min_stock", 0)

    if quantity < min_stock:
        deficit = min_stock - quantity
        print(f"[check_order_conditions] Item status: DEFICIT (need {deficit} more)")
        return f"ДЕФИЦИТ: осталось {quantity}, нужно минимум {min_stock} (не хватает {deficit})"

    surplus = quantity - min_stock
    print(f"[check_order_conditions] Item status: OK (surplus {surplus})")
    return f"В НОРМЕ: остаток {quantity}, минимум {min_stock} (запас {surplus})"


def _format_items(items_to_order: list[dict]) -> str:
    """Список товаров с готовыми числами — чтобы LLM не пересчитывала."""
    if not items_to_order:
        return "Товары для заказа не указаны."

    lines = []
    for it in items_to_order:
        lines.append(
            f"- {it.get('product_name', '?')} — "
            f"{it.get('quantity', 0)} {it.get('unit_of_measure', '')} × "
            f"{it.get('unit_price', 0)} = {it.get('item_cost', 0):.2f} руб."
        )
    return "\n".join(lines)


def _format_threshold(total_cost: float, min_order_amount: float | None) -> str:
    """Сравнение суммы заказа с порогом — числа считает Python."""
    if min_order_amount is None:
        return "Минимальная сумма в договоре не найдена — уточнить у поставщика."

    if total_cost >= min_order_amount:
        verdict = "ПРЕВЫШАЕТ порог — заказ возможен."
    else:
        verdict = "НЕ превышает порог — заказ невозможен."

    return (
        f"Минимальная сумма: {min_order_amount:.2f} руб. "
        f"Сумма заказа: {total_cost:.2f} руб. {verdict}"
    )


SYSTEM_PROMPT = """Ты — AI-оператор склада канцелярии.
Твоя задача — объяснить пользователю, можно ли заказывать у поставщика.

ВАЖНЫЕ ПРАВИЛА:
1. Все числа (сумма заказа, порог, стоимости позиций) уже посчитаны и даны тебе.
2. НЕ ПЕРЕСЧИТЫВАЙ их. Используй ровно те значения, что в запросе.
3. ДЕФИЦИТ на складе = причина заказать, а не проблема.
4. Проанализируй: договор, качество, историю заказов, статус поставщика.
5. Дай чёткий вывод:
   - МОЖНО ЗАКАЗЫВАТЬ
   - НЕ РЕКОМЕНДУЕТСЯ
   - ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА
6. Будь кратким, не выдумывай данные."""


def check_order_conditions(state: GraphState) -> dict:
    """
    Узел: check_order_conditions.
    Проверяет условия заказа у поставщика и формирует рекомендацию.
    """
    print(f"[check_order_conditions] Checking order conditions for supplier: {state.target_supplier_id}")

    # 1. Найти поставщика в state
    supplier_data = next(
        (s for s in state.suppliers if s.get("supplier_id") == state.target_supplier_id),
        None,
    )
    if not supplier_data:
        return {
            "answer": f"Поставщик {state.target_supplier_id} не найден в базе данных.",
            "errors": state.errors + [f"Supplier {state.target_supplier_id} not found"],
            "route_trace": state.route_trace + ["check_order_conditions: supplier not found"],
        }

    # 2. Файлы поставщика
    supplier_files = state.supplier_files
    contract = supplier_files.get("contract", "Нет данных")
    quality = supplier_files.get("quality", "Нет данных")
    history = supplier_files.get("history", "Нет данных")

    # 3. Числа — считает код
    items_to_order = state.items_to_order or []
    total_cost = state.total_cost or 0.0
    min_order_amount = _parse_min_order_amount(contract)

    items_text = _format_items(items_to_order)
    threshold_text = _format_threshold(total_cost, min_order_amount)

    # 4. Статус конкретного товара (если указан)
    item_status = _get_item_status(state)

    # 5. LLM — только текст
    try:
        llm = get_llm(temperature=0.3)

        user_prompt = f"""Поставщик: {supplier_data.get('company_name', '?')} ({state.target_supplier_id})

Данные поставщика из Excel:
{supplier_data}

Условия договора (contract.txt):
{contract}

Качество товаров (quality_notes.txt):
{quality}

История заказов (order_history.txt):
{history}

{f"Статус товара {state.target_item_id}: {item_status}" if item_status else ""}

ТОВАРЫ ДЛЯ ЗАКАЗА (числа уже посчитаны, не пересчитывай):
{items_text}

ИТОГО: {total_cost:.2f} руб.

ПРОВЕРКА ПОРОГА: {threshold_text}

Напиши краткий анализ и вывод."""

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        response = llm.invoke(messages)
        answer = response.content

        print(f"[check_order_conditions] Analysis completed ({len(answer)} chars)")

        return {
            "answer": answer,
            "route_trace": state.route_trace + [
                f"check_order_conditions: total={total_cost}, min={min_order_amount}"
            ],
        }

    except Exception as e:
        print(f"[check_order_conditions] Error: {e}")
        return {
            "answer": f"Ошибка при проверке условий заказа: {str(e)}",
            "errors": state.errors + [f"check_order_conditions error: {str(e)}"],
            "route_trace": state.route_trace + ["check_order_conditions: error"],
        }