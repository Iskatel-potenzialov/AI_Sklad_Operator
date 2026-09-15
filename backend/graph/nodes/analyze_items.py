"""
Узел: analyze_items
LLM-анализ проблемных товаров на складе.
"""
from langchain_core.messages import HumanMessage, SystemMessage
from backend.graph.state import GraphState
from backend.graph.nodes.utils import get_llm


def analyze_items(state: GraphState) -> dict:
    """
    Узел: analyze_items
    LLM анализирует проблемные товары и даёт рекомендации.
    """
    print(f"[analyze_items] Analyzing {len(state.problem_items)} problem items")
    
    if not state.problem_items:
        return {
            "answer": "Проблемных товаров на складе не обнаружено. Все товары в наличии!",
            "route_trace": state.route_trace + ["analyze_items: no problems"],
        }
    
    try:
        llm = get_llm(temperature=0.3)
        
        # Формируем контекст из проблемных товаров
        items_context = []
        for pi in state.problem_items[:15]:  # Ограничиваем до 15 товаров
            items_context.append(
                f"Товар: {pi.get('product_name', 'N/A')} (ID: {pi.get('item_id', 'N/A')})\n"
                f"  Категория: {pi.get('category', 'N/A')}\n"
                f"  Проблемы: {', '.join(pi.get('problems', []))}\n"
                f"  Текущий остаток: {pi.get('quantity', 0)} {pi.get('unit_of_measure', '')}\n"
                f"  Минимальный остаток: {pi.get('min_stock', 0)} {pi.get('unit_of_measure', '')}\n"
                f"  Поставщик: {pi.get('supplier_id', 'N/A')}\n"
                f"  Последний заказ: {pi.get('last_ordered', 'N/A')}"
            )
        
        items_text = "\n\n".join(items_context)
        
        # Формируем контекст из поставщиков
        suppliers_context = []
        if hasattr(state, 'suppliers') and state.suppliers:
            for supplier in state.suppliers[:5]:  # Ограничиваем до 5 поставщиков
                suppliers_context.append(
                    f"Поставщик: {supplier.get('company_name', 'N/A')} (ID: {supplier.get('supplier_id', 'N/A')})\n"
                    f"  Рейтинг: {supplier.get('rating', 'N/A')}/5.0\n"
                    f"  Последний контакт: {supplier.get('last_contact', 'N/A')}\n"
                    f"  Статус: {supplier.get('status', 'N/A')}"
                )
        
        suppliers_text = "\n\n".join(suppliers_context) if suppliers_context else "Нет данных о поставщиках"
        
        system_prompt = """Ты — AI-оператор склада канцелярии.
Проанализируй проблемные товары и дай реалистичные рекомендации.

ВАЖНЫЕ ПРАВИЛА:
1. Товары с quantity < min_stock — КРИТИЧНЫЕ (нужно срочно заказать)
2. Товары не заказываемые > 90 дней — возможно, не нужны (пересмотреть min_stock)
3. Поставщики не отвечавшие > 30 дней — ПРОБЛЕМНЫЕ (найти альтернативу)
4. Для критичных товаров предложи КОНКРЕТНЫЕ действия:
   - Связаться с поставщиком
   - Разместить заказ
   - Найти альтернативного поставщика
   - Пересмотреть min_stock

Для каждого проблемного товара укажи:
1. Краткое описание проблемы
2. Уровень срочности (критический/высокий/средний/низкий)
3. Конкретные рекомендации по действиям
4. Предлагаемое действие (если нужно)

Отвечай структурированно, по-русски. Будь реалистичен."""
        
        user_prompt = f"""Проанализируй следующие проблемные товары на складе:

{items_text}

Информация о поставщиках:
{suppliers_text}

Дай рекомендации по каждому проблемному товару."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        response = llm.invoke(messages)
        answer = response.content
        
        print(f"[analyze_items] Analysis generated ({len(answer)} chars)")
        
        return {
            "answer": answer,
            "route_trace": state.route_trace + ["analyze_items: done"],
        }
        
    except Exception as e:
        print(f"[analyze_items] Error: {e}")
        return {
            "answer": f"Ошибка при анализе товаров: {str(e)}",
            "errors": state.errors + [f"analyze_items error: {str(e)}"],
            "route_trace": state.route_trace + ["analyze_items: error"],
        }
