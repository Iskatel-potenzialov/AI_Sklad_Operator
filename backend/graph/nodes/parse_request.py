"""
parse_request — LLM-классификация намерения пользователя с использованием Function Calling.
"""
import json
from langchain_core.messages import HumanMessage
from backend.graph.state import GraphState
from backend.graph.nodes.utils import get_llm


# Определяем tool для парсинга запроса
PARSE_REQUEST_TOOL = {
    "type": "function",
    "function": {
        "name": "parse_request",
        "description": (
            "Определи намерение пользователя и извлеки сущности "
            "(ID товара, ID поставщика, новое значение min_stock)"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": [
                        "general_question",
                        "inventory_analysis",
                        "check_order_conditions",
                        "confirm_order",
                        "update_min_stock",
                        "search_knowledge",
],
                    "description": """Намерение пользователя. Правила классификации:
- general_question: общие вопросы о возможностях системы
  Примеры: "Что ты умеешь?", "Как ты работаешь?"
- inventory_analysis: запрос информации о товарах на складе
  Примеры: "Какие товары надо заказать?", "Каких товаров не хватает?"
- check_order_conditions: проверка условий заказа у поставщика
  Примеры: "Можно ли заказать item_002 у supplier_003?", "Проверь условия supplier_001"
- confirm_order: желание СОЗДАТЬ РЕАЛЬНЫЙ заказ
  Примеры: "Закажи у supplier_001", "Размести заказ у supplier_002"
- update_min_stock: ИЗМЕНИТЬ минимальный остаток товара в Excel
  Примеры: "Поменяй min_stock у item_012 на 50", "Установи item_005 минимум 100",
           "Сделай у item_020 минимум 25 штук"
- search_knowledge: вопрос о НОРМАХ, ПРАВИЛАХ, ИНСТРУКЦИЯХ, документах склада.
  То, чего нет в Excel. Примеры: "Какие нормы хранения бумаги?",
  "Какая температура на складе?", "Ширина проездов в складе?"
""",
                },
                "target_item_id": {
                    "type": ["string", "null"],
                    "description": "ID товара (item_XXX) или null если не указан",
                },
                "target_supplier_id": {
                    "type": ["string", "null"],
                    "description": "ID поставщика (supplier_XXX) или null если не указан",
                },
                "new_min_stock": {
                    "type": ["integer", "null"],
                    "description": """Новое значение минимального остатка.
Извлекай ТОЛЬКО для intent=update_min_stock.
Примеры: "поменяй на 50" → 50, "установи минимальный остаток 100 штук" → 100.
Иначе null.""",
                },
                "requires_item_data": {
                    "type": "boolean",
                    "description": "Нужны ли данные о товарах",
                },
                "requires_supplier_data": {
                    "type": "boolean",
                    "description": "Нужны ли данные о поставщиках",
                },
            },
            "required": ["intent"],
        },
    },
}


def _parse_tool_arguments(tool_call: dict) -> dict:
    """Извлекает аргументы tool_call в виде dict (args может быть str или dict)."""
    args = tool_call.get("args", {})
    if isinstance(args, str):
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            return {}
    return args or {}


def _fallback_general(reason: str, state: GraphState, errors: list[str] | None = None) -> dict:
    """Fallback: считаем запрос общим вопросом."""
    print(f"[parse_request] Fallback to general_question ({reason})")
    result = {
        "intent": "general_question",
        "target_item_id": None,
        "target_supplier_id": None,
        "new_min_stock": None,
        "scope": "no_data",
        "route_trace": state.route_trace + [f"parse_request: fallback ({reason})"],
    }
    if errors:
        result["errors"] = errors
    return result


def parse_request(state: GraphState) -> dict:
    """
    Узел: parse_request.
    LLM определяет намерение пользователя с использованием Function Calling.
    """
    print(f"[parse_request] Parsing request for run {state.run_id}")
    print(f"[parse_request] Request: {state.user_request[:100]}")

    try:
        llm = get_llm(temperature=0.1)

        system_prompt = (
            "Ты — классификатор запросов для AI-оператора склада канцелярии. "
            "Определи намерение пользователя и извлеки сущности."
        )

        messages = [
            HumanMessage(content=f"{system_prompt}\n\nЗапрос: {state.user_request}"),
        ]

        response = llm.invoke(messages, tools=[PARSE_REQUEST_TOOL])

        # Fallback: LLM не вызвала tool
        if not response.tool_calls:
            return _fallback_general("no tool call", state)

        arguments = _parse_tool_arguments(response.tool_calls[0])

        intent = arguments.get("intent", "general_question")
        target_item_id = arguments.get("target_item_id")
        target_supplier_id = arguments.get("target_supplier_id")
        new_min_stock = arguments.get("new_min_stock")
        requires_item_data = arguments.get("requires_item_data", False)
        requires_supplier_data = arguments.get("requires_supplier_data", False)

        print(f"[parse_request] Intent: {intent}")
        print(f"[parse_request] Target item: {target_item_id}")
        print(f"[parse_request] Target supplier: {target_supplier_id}")
        print(f"[parse_request] New min_stock: {new_min_stock}")
        print(f"[parse_request] Requires item data: {requires_item_data}")
        print(f"[parse_request] Requires supplier data: {requires_supplier_data}")

        return {
            "intent": intent,
            "target_item_id": target_item_id,
            "target_supplier_id": target_supplier_id,
            "new_min_stock": new_min_stock,
            "scope": "with_data" if (requires_item_data or requires_supplier_data) else "no_data",
            "route_trace": state.route_trace + [f"parse_request: intent={intent}"],
        }

    except Exception as e:
        print(f"[parse_request] Error: {e}")
        import traceback
        traceback.print_exc()
        return _fallback_general(
            "exception",
            state,
            errors=state.errors + [f"parse_request error: {str(e)}"],
        )