"""
Узел: find_problem_items
Детерминированно находит товары с проблемами на складе.

Критерии проблемности:
1. quantity < min_stock (заканчивается)
2. last_ordered > 90 дней назад (не заказывали давно)
3. supplier.last_contact > 30 дней назад (поставщик не отвечает)
"""
from datetime import datetime, timedelta
from typing import List, Dict
from backend.graph.state import GraphState


def find_problem_items(state: GraphState) -> dict:
    """
    Узел: find_problem_items
    Детерминированно находит товары с проблемами.
    
    Критерии:
    - quantity < min_stock (заканчивается)
    - last_ordered > 90 дней (не заказывали)
    - supplier не отвечал > 30 дней
    """
    print(f"[find_problem_items] Analyzing {len(state.items)} items")
    
    problem_items = []
    today = datetime.now()
    threshold_90_days = today - timedelta(days=90)
    threshold_30_days = today - timedelta(days=30)
    
    for item in state.items:
        problems = []
        
        # 1. Проверка: quantity < min_stock (заканчивается)
        quantity = item.get("quantity", 0)
        min_stock = item.get("min_stock", 0)
        if isinstance(quantity, (int, float)) and isinstance(min_stock, (int, float)):
            if quantity < min_stock:
                deficit = min_stock - quantity
                problems.append(f"Заканчивается: осталось {quantity}, минимум {min_stock} (дефицит {deficit})")
        
        # 2. Проверка: last_ordered > 90 дней (не заказывали)
        last_ordered = item.get("last_ordered")
        if last_ordered:
            try:
                if isinstance(last_ordered, str):
                    order_date = datetime.strptime(last_ordered, "%Y-%m-%d")
                else:
                    order_date = last_ordered
                
                if order_date < threshold_90_days:
                    days_since = (today - order_date).days
                    problems.append(f"Не заказывали {days_since} дней (порог 90 дней)")
            except (ValueError, TypeError):
                pass
        
        # 3. Проверка: supplier не отвечал > 30 дней
        # Для этого нужно получить данные поставщика из state.suppliers
        supplier_id = item.get("supplier_id")
        if supplier_id and hasattr(state, 'suppliers') and state.suppliers:
            supplier = next((s for s in state.suppliers if s.get("supplier_id") == supplier_id), None)
            if supplier:
                last_contact = supplier.get("last_contact")
                if last_contact:
                    try:
                        if isinstance(last_contact, str):
                            contact_date = datetime.strptime(last_contact, "%Y-%m-%d")
                        else:
                            contact_date = last_contact
                        
                        if contact_date < threshold_30_days:
                            days_since = (today - contact_date).days
                            problems.append(f"Поставщик не отвечал {days_since} дней (порог 30 дней)")
                    except (ValueError, TypeError):
                        pass
        
        # Если есть проблемы — добавляем в список
        if problems:
            problem_items.append({
                **item,
                "problems": problems,
                "problem_count": len(problems),
            })
    
    # Сортируем по количеству проблем (убывание)
    problem_items.sort(key=lambda i: i["problem_count"], reverse=True)
    
    print(f"[find_problem_items] Found {len(problem_items)} problem items")
    for pi in problem_items[:5]:
        print(f"  - {pi.get('product_name')}: {', '.join(pi['problems'])}")
    
    return {
        "problem_items": problem_items,
        "route_trace": state.route_trace + [f"find_problem_items: {len(problem_items)} found"],
    }
