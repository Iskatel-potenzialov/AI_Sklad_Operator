"""
Узел: route_after_check
Маршрутизирует после проверки условий заказа.
"""
from backend.graph.state import GraphState


def route_after_check(state: GraphState) -> str:
    """
    После проверки условий заказа определяет следующий шаг:
    - check_order_conditions → END (показать результат)
    - confirm_order → confirm_order (для подтверждения)
    """
    intent = state.intent or "check_order_conditions"
    
    print(f"[route_after_check] Routing after check based on intent: {intent}")
    
    if intent == "check_order_conditions":
        print(f"[route_after_check] → END")
        return "end"
    
    elif intent == "confirm_order":
        print(f"[route_after_check] → confirm_order")
        return "confirm_order"
    
    else:
        print(f"[route_after_check] Unknown intent, fallback → END")
        return "end"
