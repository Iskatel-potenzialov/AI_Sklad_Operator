"""
route_request — детерминированная маршрутизация на основе intent.
Это НЕ узел, а функция маршрутизации для LangGraph.
"""
from backend.graph.state import GraphState


def route_request(state: GraphState) -> str:
    """
    Функция маршрутизации.
    Определяет следующий узел на основе intent.

    Возвращает имя следующего узла.
    """
    intent = state.intent or "general_question"

    print(f"[route_request] Routing based on intent: {intent}")

    if intent == "general_question":
        print(f"[route_request] → answer_general")
        return "answer_general"

    elif intent == "inventory_analysis":
        print(f"[route_request] → load_items")
        return "load_items"

    elif intent == "check_order_conditions":
        print(f"[route_request] → load_items (далее route_after_load → load_supplier_files)")
        return "load_items"

    elif intent == "confirm_order":
        print(f"[route_request] → load_items (далее route_after_load → load_supplier_files)")
        return "load_items"
    
    elif intent == "update_min_stock":
        print(f"[route_request] → load_items (далее prepare_update)")
        return "load_items"
    
    elif intent == "search_knowledge":
        print(f"[route_request] → search_knowledge")
        return "search_knowledge"

    else:
        print(f"[route_request] Unknown intent, fallback → answer_general")
        return "answer_general"