"""
Узел: load_items
Загружает товары и поставщиков через MCP.
Считает items_to_order и total_cost для сценариев заказа.
"""
from backend.graph.state import GraphState
from backend.mcp_client.client import get_mcp_client


def _load_items_via_mcp(state: GraphState, mcp_client, mcp_results: dict, errors: list) -> list:
    """Загружает либо конкретный товар (target_item_id), либо все товары."""
    if state.target_item_id:
        print(f"[load_items] Loading specific item: {state.target_item_id}")
        result = mcp_client.get_item(state.target_item_id)

        if result.get("success"):
            item_data = result.get("item")
            items = [item_data] if item_data else []
            mcp_results["items"] = {
                "status": "success",
                "message": f"Загружен товар {state.target_item_id}",
            }
            return items

        error_msg = result.get("error", "Неизвестная ошибка")
        error_code = result.get("error_code", "UNKNOWN_ERROR")
        errors.append(f"MCP error ({error_code}): {error_msg}")
        mcp_results["items"] = {
            "status": "error",
            "message": f"Ошибка загрузки: {error_msg}",
        }
        return []

    print(f"[load_items] Loading all items")
    result = mcp_client.get_items()

    if result.get("success"):
        items = result.get("items", [])
        mcp_results["items"] = {
            "status": "success",
            "message": f"Загружено {len(items)} товаров",
        }
        return items

    error_msg = result.get("error", "Неизвестная ошибка")
    error_code = result.get("error_code", "UNKNOWN_ERROR")
    errors.append(f"MCP error ({error_code}): {error_msg}")
    mcp_results["items"] = {
        "status": "error",
        "message": f"Ошибка загрузки: {error_msg}",
    }
    return []


def _load_suppliers_via_mcp(mcp_client, mcp_results: dict) -> list:
    """Загружает список поставщиков."""
    print(f"[load_items] Loading suppliers")
    result = mcp_client.get_suppliers()

    if result.get("success"):
        suppliers = result.get("suppliers", [])
        mcp_results["suppliers"] = {
            "status": "success",
            "message": f"Загружено {len(suppliers)} поставщиков",
        }
        return suppliers

    error_msg = result.get("error", "Неизвестная ошибка")
    mcp_results["suppliers"] = {
        "status": "error",
        "message": f"Ошибка загрузки поставщиков: {error_msg}",
    }
    return []


def _build_order(items: list[dict], predicate) -> tuple[list[dict], float]:
    """
    Формирует список товаров к заказу и считает сумму.
    Берёт только дефицитные товары (quantity < min_stock), прошедшие predicate.
    """
    items_to_order: list[dict] = []
    total_cost = 0.0

    for item in items:
        if not predicate(item):
            continue

        quantity = item.get("quantity", 0)
        min_stock = item.get("min_stock", 0)
        if quantity >= min_stock:
            continue

        deficit = min_stock - quantity
        unit_price = item.get("unit_price", 0)
        item_cost = deficit * unit_price
        total_cost += item_cost

        items_to_order.append({
            "item_id": item.get("item_id"),
            "product_name": item.get("product_name"),
            "quantity": deficit,
            "unit_of_measure": item.get("unit_of_measure"),
            "unit_price": unit_price,
            "item_cost": item_cost,
        })

    return items_to_order, total_cost


def _prepare_items_to_order(state: GraphState, items: list[dict]) -> tuple[list[dict], float]:
    """
    Формирует items_to_order и total_cost в зависимости от intent:
      - confirm_order + target_supplier_id → все дефицитные товары этого поставщика
      - check_order_conditions + target_item_id → только указанный товар
    """
    if state.intent == "confirm_order" and state.target_supplier_id:
        print(f"[load_items] Preparing items for order from {state.target_supplier_id}")
        items_to_order, total_cost = _build_order(
            items,
            predicate=lambda it: it.get("supplier_id") == state.target_supplier_id,
        )
        print(f"[load_items] Prepared {len(items_to_order)} items for order, total cost: {total_cost} руб.")
        return items_to_order, total_cost

    if state.intent == "check_order_conditions" and state.target_item_id:
        print(f"[load_items] Preparing potential order for item {state.target_item_id}")
        items_to_order, total_cost = _build_order(
            items,
            predicate=lambda it: it.get("item_id") == state.target_item_id,
        )
        print(f"[load_items] Potential order: {len(items_to_order)} items, total cost: {total_cost} руб.")
        return items_to_order, total_cost

    return [], 0.0


def load_items(state: GraphState) -> dict:
    """
    Узел: load_items.
    Загружает товары и поставщиков через MCP, считает items_to_order и total_cost.
    """
    print(f"[load_items] Loading items for run {state.run_id}")

    mcp_results = dict(state.mcp_results)
    errors = list(state.errors)
    mcp_client = get_mcp_client()

    items = _load_items_via_mcp(state, mcp_client, mcp_results, errors)
    suppliers = _load_suppliers_via_mcp(mcp_client, mcp_results)
    items_to_order, total_cost = _prepare_items_to_order(state, items)

    print(f"[load_items] Loaded {len(items)} items, {len(suppliers)} suppliers")

    return {
        "items": items,
        "suppliers": suppliers,
        "items_to_order": items_to_order,
        "total_cost": total_cost,
        "mcp_results": mcp_results,
        "errors": errors,
        "route_trace": state.route_trace + [
            f"load_items: {len(items)} items, {len(suppliers)} suppliers, "
            f"{len(items_to_order)} to order, total cost: {total_cost} руб."
        ],
    }