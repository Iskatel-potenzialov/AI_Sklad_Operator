"""
Узел: route_after_load
Маршрутизирует после загрузки данных в зависимости от intent.
"""
from backend.graph.state import GraphState


def route_after_load(state: GraphState) -> str:
    """
    После загрузки данных определяет следующий шаг:
    - inventory_analysis → find_problem_items
    - check_order_conditions → load_supplier_files
    - confirm_order → load_supplier_files
    """
    intent = state.intent or "inventory_analysis"
    
    print(f"[route_after_load] Routing after load based on intent: {intent}")
    
    if intent == "update_min_stock":
        print(f"[route_after_load] → prepare_update")
        return "prepare_update"
    
    
    if intent == "inventory_analysis":
        print(f"[route_after_load] → find_problem_items")
        return "find_problem_items"
    
    elif intent == "check_order_conditions":
        print(f"[route_after_load] → load_supplier_files")
        return "load_supplier_files"
    
    elif intent == "confirm_order":
        print(f"[route_after_load] → load_supplier_files")
        return "load_supplier_files"
    
    else:
        print(f"[route_after_load] Unknown intent, fallback → find_problem_items")
        return "find_problem_items"
