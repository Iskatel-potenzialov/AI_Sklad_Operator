"""
answer_general — ответ на общие вопросы без загрузки данных клиентов.
"""
from langchain_core.messages import HumanMessage, SystemMessage
from backend.graph.state import GraphState
from backend.graph.nodes.utils import get_llm


def answer_general(state: GraphState) -> dict:
    """
    Узел: answer_general
    Отвечает на общие вопросы о возможностях системы.
    НЕ загружает данные клиентов.
    """
    print(f"[answer_general] Answering general question for run {state.run_id}")
    
    try:
        llm = get_llm(temperature=0.5)
        
        system_prompt = """Ты — AI-оператор склада канцелярии.
Отвечай на вопросы пользователя о своих возможностях.

Что ты умеешь:
- Анализировать складские запасы товаров
- Находить товары с дефицитом (quantity < min_stock)
- Проверять условия заказа у поставщиков
- Анализировать качество поставщиков и историю заказов
- Формировать рекомендации по заказу товаров
- Автоматизировать процесс заказа с подтверждением пользователя

Отвечай кратко, по-русски, дружелюбно. Не выдумывай данные о товарах."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state.user_request),
        ]
        
        response = llm.invoke(messages)
        answer = response.content
        
        print(f"[answer_general] Answer generated ({len(answer)} chars)")
        
        return {
            "answer": answer,
            "route_trace": state.route_trace + ["answer_general"],
        }
        
    except Exception as e:
        print(f"[answer_general] Error: {e}")
        return {
            "answer": f"Извините, произошла ошибка: {str(e)}",
            "errors": state.errors + [f"answer_general error: {str(e)}"],
            "route_trace": state.route_trace + ["answer_general: error"],
        }
