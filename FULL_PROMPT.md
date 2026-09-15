# ПОЛНЫЙ ПРОМТ ДЛЯ СОЗДАНИЯ AI-ОПЕРАТОРА СКЛАДА КАНЦЕЛЯРИИ С НУЛЯ

## ВВОДНАЯ ЧАСТЬ

Создай полноценный проект AI-оператора склада канцелярии с нуля. Проект должен включать backend на Python (FastAPI + LangGraph + OpenAI + MCP) и frontend на React (Vite + TypeScript + Tailwind CSS).

Следуй всем инструкциям ниже пошагово. Создавай все файлы последовательно, проверяй сборку после каждого этапа.

---

## ЭТАП 1: БАЗОВЫЙ КАРКАС (Backend + Frontend + LangGraph + SSE)

### 1.1. Структура проекта

Создай следующую структуру:

```
project/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── run_manager.py
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py
│   │   ├── workflow.py
│   │   └── nodes/
│   │       ├── __init__.py
│   │       ├── utils.py
│   │       ├── parse_request.py
│   │       ├── route_request.py
│   │       ├── answer_general.py
│   │       ├── load_items.py
│   │       ├── find_problem_items.py
│   │       ├── analyze_items.py
│   │       ├── load_supplier_files.py
│   │       ├── check_order_conditions.py
│   │       ├── confirm_order.py
│   │       ├── route_after_load.py
│   │       └── route_after_check.py
│   ├── mcp_server/
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── items_service.py
│   │   ├── suppliers_service.py
│   │   ├── schemas.py
│   │   └── validation.py
│   ├── mcp_client/
│   │   ├── __init__.py
│   │   └── client.py
│   ├── main.py
│   ├── config.py
│   ├── .env.example
│   └── requirements.txt
├── src/
│   ├── components/
│   │   ├── Header.tsx
│   │   ├── RunInput.tsx
│   │   ├── AnswerPanel.tsx
│   │   ├── ExecutionLog.tsx
│   │   └── ActionApproval.tsx
│   ├── App.tsx
│   ├── main.tsx
│   ├── index.css
│   └── types.ts
├── data/
│   ├── items.xlsx
│   ├── suppliers.xlsx
│   └── suppliers/
│       ├── supplier_001/
│       │   ├── contract.txt
│       │   ├── quality_notes.txt
│       │   └── order_history.txt
│       └── ... (supplier_002 - supplier_005)
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

### 1.2. Backend: requirements.txt

Создай файл `backend/requirements.txt`:

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
langgraph==0.2.60
langchain==0.3.14
langchain-openai==0.3.0
python-dotenv==1.0.1
pydantic==2.10.4
sse-starlette==2.1.3
httpx==0.27.2
openpyxl==3.1.5
mcp[cli]>=2.0.0
```

### 1.3. Backend: config.py

Создай файл `backend/config.py`:

```python
"""
Конфигурация приложения.
Загружает переменные окружения из .env файла.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Явно указываем путь к .env (в папке backend)
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", None)

# MCP HTTP сервер
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8001"))

# Отладка — проверяем что ключ загружен
if not OPENAI_API_KEY:
    print(f"[WARNING] OPENAI_API_KEY не найден в {ENV_PATH}")
else:
    print(f"[OK] OPENAI_API_KEY загружен")
    print(f"[OK] OPENAI_MODEL = {OPENAI_MODEL}")

print(f"[OK] MCP_SERVER_URL = {MCP_SERVER_URL}")
print(f"[OK] MCP_SERVER_PORT = {MCP_SERVER_PORT}")
```

### 1.4. Backend: .env.example

Создай файл `backend/.env.example`:

```env
# OpenAI API
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
# OPENAI_API_BASE=http://localhost:11434/v1  # Для локальных моделей (Ollama, Qwen)

# Excel MCP (локальные таблицы склада)
ITEMS_FILE_PATH=data/items.xlsx
SUPPLIERS_FILE_PATH=data/suppliers.xlsx

# MCP HTTP сервер
MCP_SERVER_URL=http://localhost:8001/mcp
MCP_SERVER_PORT=8001
```

### 1.5. Backend: graph/state.py

Создай файл `backend/graph/state.py`:

```python
"""
State для LangGraph workflow склада канцелярии.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class GraphState(BaseModel):
    """Состояние графа выполнения."""
    # Идентификация
    run_id: str
    user_request: str
    
    # Маршрутизация
    intent: Optional[str] = None
    target_item_id: Optional[str] = None
    target_supplier_id: Optional[str] = None
    scope: Optional[str] = None
    
    # Данные
    items: List[Dict] = []
    suppliers: List[Dict] = []
    problem_items: List[Dict] = []
    supplier_files: Dict[str, str] = {}
    
    # Анализ
    analysis: Optional[Dict] = None
    recommended_actions: List[Dict] = []
    pending_action: Optional[Dict] = None
    action_approved: bool = False
    
    # Результат
    answer: Optional[str] = None
    order_confirmation: Optional[Dict] = None
    
    # Метаданные
    errors: List[str] = []
    status: str = "pending"
    route_trace: List[str] = []
    
    # Стоимость заказа
    items_to_order: List[Dict] = []
    total_cost: float = 0

    class Config:
        arbitrary_types_allowed = True
```

### 1.6. Backend: graph/nodes/utils.py

Создай файл `backend/graph/nodes/utils.py`:

```python
"""
Общие утилиты для узлов графа.
"""
from langchain_openai import ChatOpenAI
from backend.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_API_BASE


def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    """Создаёт экземпляр LLM."""
    kwargs = {
        "model": OPENAI_MODEL,
        "api_key": OPENAI_API_KEY,
        "temperature": temperature,
    }
    
    if OPENAI_API_BASE:
        kwargs["base_url"] = OPENAI_API_BASE
    
    return ChatOpenAI(**kwargs)
```

### 1.7. Backend: graph/nodes/parse_request.py

Создай файл `backend/graph/nodes/parse_request.py`:

```python
"""
parse_request — LLM-классификация намерения пользователя.
"""
import json
from langchain_core.messages import HumanMessage, SystemMessage
from backend.graph.state import GraphState
from backend.graph.nodes.utils import get_llm


def parse_request(state: GraphState) -> dict:
    """
    Узел: parse_request
    LLM определяет намерение пользователя.
    """
    print(f"[parse_request] Parsing request for run {state.run_id}")
    print(f"[parse_request] Request: {state.user_request[:100]}")
    
    try:
        llm = get_llm(temperature=0.1)
        
        system_prompt = """Ты — классификатор запросов для AI-оператора склада канцелярии.
Определи намерение пользователя и верни JSON.

Возможные намерения:
- general_question: общие вопросы о возможностях системы
- inventory_analysis: анализ складских запасов (дефицит, давность заказов)
- check_order: проверка условий заказа у поставщика
- confirm_order: подтверждение заказа товаров

Если упоминается конкретный поставщик (ID), укажи target_supplier_id.
Если упоминается конкретный товар (ID), укажи target_item_id.

Верни ТОЛЬКО JSON без пояснений:
{
  "intent": "general_question|inventory_analysis|check_order|confirm_order",
  "target_item_id": null или "item_XXX",
  "target_supplier_id": null или "supplier_XXX",
  "requires_item_data": true/false,
  "requires_supplier_data": true/false
}"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state.user_request),
        ]
        
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Парсим JSON
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        parsed = json.loads(content)
        
        intent = parsed.get("intent", "general_question")
        target_item_id = parsed.get("target_item_id")
        target_supplier_id = parsed.get("target_supplier_id")
        requires_item_data = parsed.get("requires_item_data", False)
        requires_supplier_data = parsed.get("requires_supplier_data", False)
        
        print(f"[parse_request] Intent: {intent}")
        print(f"[parse_request] Target item: {target_item_id}")
        print(f"[parse_request] Target supplier: {target_supplier_id}")
        print(f"[parse_request] Requires item data: {requires_item_data}")
        print(f"[parse_request] Requires supplier data: {requires_supplier_data}")
        
        return {
            "intent": intent,
            "target_item_id": target_item_id,
            "target_supplier_id": target_supplier_id,
            "scope": "with_data" if (requires_item_data or requires_supplier_data) else "no_data",
            "route_trace": state.route_trace + [f"parse_request: intent={intent}"],
        }
        
    except Exception as e:
        print(f"[parse_request] Error: {e}")
        return {
            "intent": "general_question",
            "target_item_id": None,
            "target_supplier_id": None,
            "scope": "no_data",
            "errors": state.errors + [f"parse_request error: {str(e)}"],
            "route_trace": state.route_trace + ["parse_request: fallback to general_question"],
        }
```

### 1.8. Backend: graph/nodes/route_request.py

Создай файл `backend/graph/nodes/route_request.py`:

```python
"""
route_request — Python-маршрутизация на основе intent.
"""
from backend.graph.state import GraphState


def route_request(state: GraphState) -> str:
    """
    Функция маршрутизации.
    Определяет следующий узел на основе intent.
    """
    intent = state.intent or "general_question"
    
    print(f"[route_request] Routing based on intent: {intent}")
    
    if intent == "general_question":
        print(f"[route_request] → answer_general")
        return "answer_general"
    
    elif intent == "inventory_analysis":
        print(f"[route_request] → load_items (for inventory analysis)")
        return "load_items"
    
    elif intent == "check_order":
        print(f"[route_request] → load_items (for order check)")
        return "load_items"
    
    elif intent == "confirm_order":
        print(f"[route_request] → load_items (for order confirmation)")
        return "load_items"
    
    else:
        print(f"[route_request] Unknown intent, fallback → answer_general")
        return "answer_general"
```

### 1.9. Backend: graph/nodes/answer_general.py

Создай файл `backend/graph/nodes/answer_general.py`:

```python
"""
Узел: answer_general
Отвечает на общие вопросы о возможностях системы.
"""
from langchain_core.messages import HumanMessage, SystemMessage
from backend.graph.state import GraphState
from backend.graph.nodes.utils import get_llm


def answer_general(state: GraphState) -> dict:
    """
    Узел: answer_general
    Отвечает на общие вопросы о возможностях системы.
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
```

### 1.10. Backend: graph/nodes/load_items.py

Создай файл `backend/graph/nodes/load_items.py`:

```python
"""
Узел: load_items
Загружает товары и поставщиков через MCP.
"""
from backend.graph.state import GraphState
from backend.mcp_client.client import get_mcp_client


def load_items(state: GraphState) -> dict:
    """
    Узел: load_items
    Загружает товары и поставщиков через MCP.
    """
    print(f"[load_items] Loading items for run {state.run_id}")
    
    mcp_results = {}
    items = []
    suppliers = []
    errors = list(state.errors)
    
    # Получаем MCP-клиент
    mcp_client = get_mcp_client()
    
    # 1. Загружаем товары
    try:
        if state.target_item_id:
            # Загружаем конкретный товар
            result = mcp_client.get_item(state.target_item_id)
            if result.get("success"):
                items = [result.get("item")]
            else:
                errors.append(f"Товар {state.target_item_id} не найден")
        else:
            # Загружаем все товары
            result = mcp_client.get_items()
            if result.get("success"):
                items = result.get("items", [])
            else:
                errors.append("Не удалось загрузить товары")
        
        mcp_results["items"] = {
            "status": "success" if result.get("success") else "error",
            "message": f"Загружено {len(items)} товаров",
        }
    except Exception as e:
        errors.append(f"Ошибка загрузки товаров: {str(e)}")
        mcp_results["items"] = {
            "status": "error",
            "message": str(e),
        }
    
    # 2. Загружаем поставщиков
    try:
        result = mcp_client.get_suppliers()
        if result.get("success"):
            suppliers = result.get("suppliers", [])
        else:
            errors.append("Не удалось загрузить поставщиков")
        
        mcp_results["suppliers"] = {
            "status": "success" if result.get("success") else "error",
            "message": f"Загружено {len(suppliers)} поставщиков",
        }
    except Exception as e:
        errors.append(f"Ошибка загрузки поставщиков: {str(e)}")
        mcp_results["suppliers"] = {
            "status": "error",
            "message": str(e),
        }
    
    print(f"[load_items] Loaded {len(items)} items, {len(suppliers)} suppliers")
    
    return {
        "items": items,
        "suppliers": suppliers,
        "mcp_results": mcp_results,
        "errors": errors,
        "route_trace": state.route_trace + [f"load_items: {len(items)} items, {len(suppliers)} suppliers"],
    }
```

### 1.11. Backend: graph/nodes/find_problem_items.py

Создай файл `backend/graph/nodes/find_problem_items.py`:

```python
"""
Узел: find_problem_items
Находит товары с дефицитом и давно не заказываемые товары.
"""
from datetime import datetime, timedelta
from backend.graph.state import GraphState


def find_problem_items(state: GraphState) -> dict:
    """
    Узел: find_problem_items
    Находит товары с дефицитом (quantity < min_stock)
    и товары, которые давно не заказывались (> 90 дней).
    """
    print(f"[find_problem_items] Analyzing {len(state.items)} items")
    
    problem_items = []
    today = datetime.now()
    threshold_90_days = today - timedelta(days=90)
    
    for item in state.items:
        problems = []
        
        # Проверка дефицита
        quantity = item.get("quantity", 0)
        min_stock = item.get("min_stock", 0)
        if quantity < min_stock:
            deficit = min_stock - quantity
            problems.append(f"Дефицит: {deficit} единиц (остаток {quantity}, минимум {min_stock})")
        
        # Проверка давности заказа
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
```

### 1.12. Backend: graph/nodes/analyze_items.py

Создай файл `backend/graph/nodes/analyze_items.py`:

```python
"""
Узел: analyze_items
LLM анализирует проблемные товары и формирует рекомендации.
"""
from langchain_core.messages import HumanMessage, SystemMessage
from backend.graph.state import GraphState
from backend.graph.nodes.utils import get_llm


def analyze_items(state: GraphState) -> dict:
    """
    Узел: analyze_items
    LLM анализирует проблемные товары и формирует рекомендации.
    """
    print(f"[analyze_items] Analyzing {len(state.problem_items)} problem items")
    
    if not state.problem_items:
        return {
            "answer": "Проблемных товаров не обнаружено. Все товары в наличии.",
            "route_trace": state.route_trace + ["analyze_items: no problems"],
        }
    
    try:
        llm = get_llm(temperature=0.3)
        
        # Формируем контекст из проблемных товаров
        items_context = []
        for pi in state.problem_items[:15]:  # Ограничиваем до 15 товаров
            items_context.append(
                f"Товар: {pi.get('product_name', 'N/A')} (ID: {pi.get('item_id', 'N/A')})\n"
                f"  Проблемы: {', '.join(pi.get('problems', []))}\n"
                f"  Поставщик: {pi.get('supplier_id', 'N/A')}\n"
                f"  Цена: {pi.get('unit_price', 0)} руб./{pi.get('unit_of_measure', 'шт')}"
            )
        
        items_text = "\n\n".join(items_context)
        
        system_prompt = """Ты — AI-оператор склада канцелярии.
Проанализируй проблемные товары и дай рекомендации.

Для каждого товара укажи:
1. Краткое описание проблемы
2. Рекомендуемое количество для заказа
3. Обоснование рекомендации

Отвечай структурированно, по-русски. Будь конкретен."""

        user_prompt = f"""Проанализируй следующие проблемные товары:

{items_text}

Дай рекомендации по каждому товару."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        response = llm.invoke(messages)
        answer = response.content
        
        print(f"[analyze_items] Analysis generated ({len(answer)} chars)")
        
        return {
            "answer": answer,
            "route_trace": state.route_trace + ["analyze_items: completed"],
        }
        
    except Exception as e:
        print(f"[analyze_items] Error: {e}")
        return {
            "answer": f"Ошибка при анализе товаров: {str(e)}",
            "errors": state.errors + [f"analyze_items error: {str(e)}"],
            "route_trace": state.route_trace + ["analyze_items: error"],
        }
```

### 1.13. Backend: graph/nodes/load_supplier_files.py

Создай файл `backend/graph/nodes/load_supplier_files.py`:

```python
"""
Узел: load_supplier_files
Загружает файлы поставщика из файловой системы.
"""
from pathlib import Path
from backend.graph.state import GraphState

# Базовая директория с файлами поставщиков
SUPPLIERS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "suppliers"


def _read_file(file_path: Path) -> str:
    """Читает текстовый файл."""
    return file_path.read_text(encoding="utf-8")


def load_supplier_files(state: GraphState) -> dict:
    """
    Загружает файлы поставщика:
    - contract.txt (условия договора)
    - quality_notes.txt (качество товаров)
    - order_history.txt (история заказов)
    """
    print(f"[load_supplier_files] Loading files for supplier: {state.target_supplier_id}")
    
    supplier_id = state.target_supplier_id
    supplier_dir = SUPPLIERS_DIR / supplier_id
    supplier_files = {}
    errors = list(state.errors)
    
    # Читаем contract.txt
    try:
        contract_path = supplier_dir / "contract.txt"
        contract_content = _read_file(contract_path)
        supplier_files["contract"] = contract_content
        print(f"[load_supplier_files] ✓ Loaded contract.txt")
    except Exception as e:
        errors.append(f"Не удалось прочитать contract.txt: {str(e)}")
        print(f"[load_supplier_files] ✗ Error reading contract.txt: {e}")
    
    # Читаем quality_notes.txt
    try:
        quality_path = supplier_dir / "quality_notes.txt"
        quality_content = _read_file(quality_path)
        supplier_files["quality"] = quality_content
        print(f"[load_supplier_files] ✓ Loaded quality_notes.txt")
    except Exception as e:
        errors.append(f"Не удалось прочитать quality_notes.txt: {str(e)}")
        print(f"[load_supplier_files] ✗ Error reading quality_notes.txt: {e}")
    
    # Читаем order_history.txt
    try:
        history_path = supplier_dir / "order_history.txt"
        history_content = _read_file(history_path)
        supplier_files["history"] = history_content
        print(f"[load_supplier_files] ✓ Loaded order_history.txt")
    except Exception as e:
        errors.append(f"Не удалось прочитать order_history.txt: {str(e)}")
        print(f"[load_supplier_files] ✗ Error reading order_history.txt: {e}")
    
    return {
        "supplier_files": supplier_files,
        "errors": errors,
        "route_trace": state.route_trace + [f"load_supplier_files: loaded {len(supplier_files)} files"],
    }
```

### 1.14. Backend: graph/nodes/check_order_conditions.py

Создай файл `backend/graph/nodes/check_order_conditions.py`:

```python
"""
Узел: check_order_conditions
Проверяет условия заказа у поставщика.
"""
from langchain_core.messages import HumanMessage, SystemMessage
from backend.graph.state import GraphState
from backend.graph.nodes.utils import get_llm


def check_order_conditions(state: GraphState) -> dict:
    """
    Узел: check_order_conditions
    Проверяет условия договора, качество и историю поставщика.
    """
    print(f"[check_order_conditions] Checking conditions for supplier: {state.target_supplier_id}")
    
    # Получаем данные поставщика
    supplier_data = None
    for supplier in state.suppliers:
        if supplier.get("supplier_id") == state.target_supplier_id:
            supplier_data = supplier
            break
    
    if not supplier_data:
        return {
            "answer": f"Поставщик {state.target_supplier_id} не найден.",
            "errors": state.errors + [f"Supplier {state.target_supplier_id} not found"],
            "route_trace": state.route_trace + ["check_order_conditions: supplier not found"],
        }
    
    # Сокращаем данные для LLM
    supplier_files = state.supplier_files
    
    contract_full = supplier_files.get("contract", "")
    contract_summary = "Условия договора: "
    if "Минимальная сумма заказа" in contract_full:
        for line in contract_full.split("\n"):
            if "Минимальная сумма" in line or "Условия оплаты" in line or "Срок поставки" in line:
                contract_summary += line.strip() + "; "
    
    quality_full = supplier_files.get("quality", "")
    quality_summary = "Качество: "
    if "Общие замечания" in quality_full:
        quality_summary += "Стабильное качество, брак менее 1%"
    else:
        quality_summary += "Хорошее качество"
    
    history_full = supplier_files.get("history", "")
    history_summary = "История: "
    if "Статистика" in history_full:
        for line in history_full.split("\n"):
            if "Всего заказов" in line or "Задержек" in line or "Возвратов" in line:
                history_summary += line.strip() + "; "
    
    try:
        llm = get_llm(temperature=0.3)
        
        system_prompt = """Ты — AI-оператор склада канцелярии.
Проверь условия заказа у поставщика и дай рекомендацию.

Проанализируй:
1. Условия договора (минимальная сумма, условия оплаты, сроки)
2. Качество товаров поставщика
3. Историю заказов (задержки, возвраты)
4. Рейтинг поставщика

Дай краткую рекомендацию (2-3 предложения): можно ли заказывать у этого поставщика?"""

        user_prompt = f"""Проверь условия заказа у поставщика:

Поставщик: {supplier_data.get('company_name', 'N/A')}
Рейтинг: {supplier_data.get('rating', 'N/A')}
Последний контакт: {supplier_data.get('last_contact', 'N/A')}

{contract_summary}

{quality_summary}

{history_summary}

Дай краткую рекомендацию: можно ли заказывать у этого поставщика?"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        response = llm.invoke(messages)
        answer = response.content
        
        print(f"[check_order_conditions] Analysis completed ({len(answer)} chars)")
        
        return {
            "answer": answer,
            "route_trace": state.route_trace + ["check_order_conditions: completed"],
        }
        
    except Exception as e:
        print(f"[check_order_conditions] Error: {e}")
        return {
            "answer": f"Ошибка при проверке условий: {str(e)}",
            "errors": state.errors + [f"check_order_conditions error: {str(e)}"],
            "route_trace": state.route_trace + ["check_order_conditions: error"],
        }
```

### 1.15. Backend: graph/nodes/confirm_order.py

Создай файл `backend/graph/nodes/confirm_order.py`:

```python
"""
Узел: confirm_order
Формирует предложение заказа и ждёт подтверждения от пользователя.
"""
from datetime import datetime
from pathlib import Path
from backend.graph.state import GraphState


def confirm_order(state: GraphState) -> dict:
    """
    Узел: confirm_order
    Формирует предложение заказа и ждёт подтверждения от пользователя.
    """
    print(f"[confirm_order] Preparing order confirmation")
    print(f"[confirm_order] state.action_approved: {state.action_approved}")
    
    # Если действие уже подтверждено - записываем заказ
    if state.action_approved:
        print(f"[confirm_order] Order approved, writing to log")
        
        # Формируем данные заказа
        order_data = {
            "timestamp": datetime.now().isoformat(),
            "supplier_id": state.target_supplier_id,
            "items": state.items_to_order,
            "total_cost": state.total_cost,
            "status": "confirmed",
            "run_id": state.run_id,
        }
        
        # Записываем в лог
        try:
            log_path = Path(__file__).parent.parent.parent.parent / "data" / "orders_log.jsonl"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(order_data, ensure_ascii=False) + "\n")
            
            print(f"[confirm_order] ✓ Order logged to {log_path}")
            
            return {
                "answer": f"✅ Заказ подтверждён и записан в лог.\n\nПоставщик: {state.target_supplier_id}\nТовары: {len(state.items_to_order)} позиций\nОбщая стоимость: {state.total_cost:.2f} руб.\nВремя: {order_data['timestamp']}",
                "order_confirmation": order_data,
                "route_trace": state.route_trace + ["confirm_order: order logged"],
            }
        except Exception as e:
            print(f"[confirm_order] ✗ Error writing log: {e}")
            return {
                "answer": f"⚠️ Заказ подтверждён, но не удалось записать в лог: {str(e)}",
                "order_confirmation": order_data,
                "errors": state.errors + [f"Failed to write log: {str(e)}"],
                "route_trace": state.route_trace + ["confirm_order: log failed"],
            }
    
    # Если действие не подтверждено - формируем предложение
    else:
        print(f"[confirm_order] Creating order proposal")
        
        # Получаем данные поставщика
        supplier_data = None
        for supplier in state.suppliers:
            if supplier.get("supplier_id") == state.target_supplier_id:
                supplier_data = supplier
                break
        
        if not supplier_data:
            return {
                "answer": f"Поставщик {state.target_supplier_id} не найден.",
                "errors": state.errors + [f"Supplier {state.target_supplier_id} not found"],
                "route_trace": state.route_trace + ["confirm_order: supplier not found"],
            }
        
        # Формируем предложение заказа
        items_summary = [
            {
                "item_id": item.get("item_id"),
                "product_name": item.get("product_name"),
                "quantity": item.get("quantity"),
                "unit_price": item.get("unit_price"),
            }
            for item in state.items_to_order
        ]
        
        proposal = {
            "action_type": "create_order",
            "supplier_id": state.target_supplier_id,
            "supplier_name": supplier_data.get("company_name", "Неизвестно"),
            "items": items_summary,
            "total_cost": state.total_cost,
            "description": f"Заказ {len(items_summary)} товаров у поставщика {supplier_data.get('company_name')} на сумму {state.total_cost:.2f} руб.",
        }
        
        print(f"[confirm_order] Proposal created: {proposal}")
        
        # Возвращаем pending_action для HITL
        return {
            "pending_action": proposal,
            "route_trace": state.route_trace + ["confirm_order: proposal created, waiting for approval"],
        }
```

### 1.16. Backend: graph/nodes/route_after_load.py

Создай файл `backend/graph/nodes/route_after_load.py`:

```python
"""
route_after_load — маршрутизация после загрузки данных.
"""
from backend.graph.state import GraphState


def route_after_load(state: GraphState) -> str:
    """
    После загрузки данных маршрутизирует в зависимости от intent.
    """
    intent = state.intent or "inventory_analysis"
    
    print(f"[route_after_load] Routing after load based on intent: {intent}")
    
    if intent == "inventory_analysis":
        print(f"[route_after_load] → find_problem_items")
        return "find_problem_items"
    
    elif intent == "check_order":
        print(f"[route_after_load] → load_supplier_files")
        return "load_supplier_files"
    
    elif intent == "confirm_order":
        print(f"[route_after_load] → load_supplier_files")
        return "load_supplier_files"
    
    else:
        print(f"[route_after_load] Unknown intent, fallback → find_problem_items")
        return "find_problem_items"
```

### 1.17. Backend: graph/nodes/route_after_check.py

Создай файл `backend/graph/nodes/route_after_check.py`:

```python
"""
route_after_check — маршрутизация после проверки условий.
"""
from backend.graph.state import GraphState


def route_after_check(state: GraphState) -> str:
    """
    После проверки условий маршрутизирует в зависимости от intent.
    """
    intent = state.intent or "check_order"
    
    print(f"[route_after_check] Routing after check based on intent: {intent}")
    
    if intent == "check_order":
        print(f"[route_after_check] → END")
        return "end"
    
    elif intent == "confirm_order":
        print(f"[route_after_check] → confirm_order")
        return "confirm_order"
    
    else:
        print(f"[route_after_check] Unknown intent, fallback → END")
        return "end"
```

### 1.18. Backend: graph/nodes/__init__.py

Создай файл `backend/graph/nodes/__init__.py`:

```python
"""
Узлы LangGraph графа склада канцелярии.
"""
from backend.graph.nodes.parse_request import parse_request
from backend.graph.nodes.route_request import route_request
from backend.graph.nodes.answer_general import answer_general
from backend.graph.nodes.load_items import load_items
from backend.graph.nodes.find_problem_items import find_problem_items
from backend.graph.nodes.analyze_items import analyze_items
from backend.graph.nodes.load_supplier_files import load_supplier_files
from backend.graph.nodes.check_order_conditions import check_order_conditions
from backend.graph.nodes.confirm_order import confirm_order
from backend.graph.nodes.route_after_load import route_after_load
from backend.graph.nodes.route_after_check import route_after_check

__all__ = [
    "parse_request",
    "route_request",
    "answer_general",
    "load_items",
    "find_problem_items",
    "analyze_items",
    "load_supplier_files",
    "check_order_conditions",
    "confirm_order",
    "route_after_load",
    "route_after_check",
]
```

### 1.19. Backend: graph/workflow.py

Создай файл `backend/graph/workflow.py`:

```python
"""
LangGraph: определение графа workflow склада канцелярии.

Граф:

START
  ↓
parse_request (LLM-классификация)
  ↓
route_request (Python-маршрутизация)
  ├─→ answer_general (общие вопросы)
  └─→ load_items (загрузка товаров и поставщиков)
        ↓
      route_after_load (маршрутизация после загрузки)
        ├─→ find_problem_items → analyze_items → END
        └─→ load_supplier_files → check_order_conditions
              ↓
            route_after_check
              ├─→ END (если check_order)
              └─→ confirm_order → END (если confirm_order)
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.graph.state import GraphState
from backend.graph.nodes.parse_request import parse_request
from backend.graph.nodes.route_request import route_request
from backend.graph.nodes.answer_general import answer_general
from backend.graph.nodes.load_items import load_items
from backend.graph.nodes.find_problem_items import find_problem_items
from backend.graph.nodes.analyze_items import analyze_items
from backend.graph.nodes.load_supplier_files import load_supplier_files
from backend.graph.nodes.check_order_conditions import check_order_conditions
from backend.graph.nodes.confirm_order import confirm_order
from backend.graph.nodes.route_after_load import route_after_load
from backend.graph.nodes.route_after_check import route_after_check


def build_graph() -> StateGraph:
    """
    Строит и компилирует LangGraph граф.
    """
    graph = StateGraph(GraphState)

    # Добавляем узлы
    graph.add_node("parse_request", parse_request)
    graph.add_node("answer_general", answer_general)
    graph.add_node("load_items", load_items)
    graph.add_node("find_problem_items", find_problem_items)
    graph.add_node("analyze_items", analyze_items)
    graph.add_node("load_supplier_files", load_supplier_files)
    graph.add_node("check_order_conditions", check_order_conditions)
    graph.add_node("confirm_order", confirm_order)

    # Стартовый переход
    graph.add_edge(START, "parse_request")

    # Маршрутизация после parse_request
    graph.add_conditional_edges(
        "parse_request",
        route_request,
        {
            "answer_general": "answer_general",
            "load_items": "load_items",
        }
    )

    # Ветка общих вопросов → END
    graph.add_edge("answer_general", END)

    # После load_items → маршрутизация
    graph.add_conditional_edges(
        "load_items",
        route_after_load,
        {
            "find_problem_items": "find_problem_items",
            "load_supplier_files": "load_supplier_files",
        }
    )

    # Ветка анализа товаров
    graph.add_edge("find_problem_items", "analyze_items")
    graph.add_edge("analyze_items", END)

    # Ветка проверки заказа
    graph.add_edge("load_supplier_files", "check_order_conditions")

    # После check_order_conditions → маршрутизация
    graph.add_conditional_edges(
        "check_order_conditions",
        route_after_check,
        {
            "end": END,
            "confirm_order": "confirm_order",
        }
    )

    # Ветка подтверждения заказа
    graph.add_edge("confirm_order", END)

    # Создаём checkpointer для HITL
    checkpointer = MemorySaver()

    # Компилируем граф с interrupt_after для HITL
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_after=["confirm_order"]
    )


# Компилированный граф (singleton)
compiled_graph = build_graph()
```

### 1.20. Backend: api/run_manager.py

Создай файл `backend/api/run_manager.py`:

```python
"""
Менеджер запусков (runs).
Хранит состояние активных запусков и их события.
"""
import uuid
import asyncio
from typing import AsyncGenerator
from dataclasses import dataclass, field


@dataclass
class Run:
    """Представляет один запуск workflow."""
    run_id: str
    user_request: str
    status: str = "pending"  # pending | running | finished | error | waiting_approval
    events: list[dict] = field(default_factory=list)
    event_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    # Для HITL
    pending_action: dict | None = None
    graph_state: dict | None = None


class RunManager:
    """
    Управляет запусками workflow.
    Хранит активные runs и позволяет подписываться на их события через SSE.
    """

    def __init__(self):
        self._runs: dict[str, Run] = {}

    def create_run(self, user_request: str) -> Run:
        """Создаёт новый запуск и возвращает его."""
        run_id = str(uuid.uuid4())
        run = Run(run_id=run_id, user_request=user_request)
        self._runs[run_id] = run
        return run

    def get_run(self, run_id: str) -> Run | None:
        """Возвращает запуск по ID или None."""
        return self._runs.get(run_id)

    async def emit_event(self, run_id: str, event: dict):
        """
        Добавляет событие в run и уведомляет подписчиков через очередь.
        """
        run = self._runs.get(run_id)
        if not run:
            print(f"[emit_event] Run {run_id} not found!")
            return
        run.events.append(event)
        await run.event_queue.put(event)
        print(f"[emit_event] Event queued: {event.get('type')}")

    async def event_stream(self, run_id: str) -> AsyncGenerator[dict, None]:
        """
        Генератор событий для SSE.
        Возвращает события по мере их появления.
        Завершается когда run получает статус finished или error.
        """
        run = self._runs.get(run_id)
        if not run:
            yield {"type": "error", "message": "Run not found"}
            return

        while True:
            try:
                # Ждём событие с таймаутом
                event = await asyncio.wait_for(run.event_queue.get(), timeout=120.0)
                yield event

                # Если run завершён — выходим
                if event.get("type") in ("run_finished", "error"):
                    break
            except asyncio.TimeoutError:
                # Если долго нет событий — отправляем heartbeat
                yield {"type": "heartbeat"}
                # Проверяем, не завершился ли run
                if run.status in ("finished", "error"):
                    break


# Глобальный менеджер запусков
run_manager = RunManager()
```

### 1.21. Backend: api/routes.py

Создай файл `backend/api/routes.py`:

```python
"""
FastAPI роуты для AI-оператора склада.
"""
import asyncio
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.api.run_manager import run_manager
from backend.graph.workflow import compiled_graph
from backend.graph.state import GraphState

router = APIRouter(prefix="/api")


class RunRequest(BaseModel):
    """Запрос на запуск workflow."""
    request: str


class RunResponse(BaseModel):
    """Ответ с ID запуска."""
    run_id: str
    status: str


class ApprovalRequest(BaseModel):
    """Запрос на подтверждение/отклонение действия."""
    approved: bool


# Описания узлов для UI
NODE_LABELS = {
    "parse_request": "Определение задачи",
    "answer_general": "Общий ответ",
    "load_items": "Загрузка товаров",
    "find_problem_items": "Поиск проблемных товаров",
    "analyze_items": "Анализ товаров",
    "load_supplier_files": "Загрузка файлов поставщика",
    "check_order_conditions": "Проверка условий заказа",
    "confirm_order": "Подтверждение заказа",
}


@router.post("/run", response_model=RunResponse)
async def create_run(req: RunRequest):
    """
    POST /api/run
    Создаёт новый запуск workflow.
    """
    if not req.request.strip():
        raise HTTPException(status_code=400, detail="Request cannot be empty")

    # Создаём run
    run = run_manager.create_run(req.request.strip())

    # Отправляем событие run_started
    await run_manager.emit_event(run.run_id, {
        "type": "run_started",
        "run_id": run.run_id,
    })
    run.status = "running"

    # Запускаем workflow в фоне
    print(f"[create_run] Starting workflow for run {run.run_id}")
    task = asyncio.create_task(_execute_workflow(run.run_id, req.request.strip()))
    print(f"[create_run] Task created: {task}")

    return RunResponse(run_id=run.run_id, status="running")


@router.post("/run/{run_id}/approve")
async def approve_action(run_id: str, req: ApprovalRequest):
    """
    POST /api/run/{run_id}/approve
    Подтверждает или отклоняет ожидающее действие (HITL).
    """
    run = run_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if run.status != "waiting_approval":
        raise HTTPException(status_code=400, detail="Run is not waiting for approval")
    
    print(f"[approve_action] Run {run_id}: approved={req.approved}")
    
    # Сохраняем approved в pending_action
    if run.pending_action:
        run.pending_action["approved"] = req.approved
        print(f"[approve_action] Updated pending_action: {run.pending_action}")
    
    # Отправляем событие
    await run_manager.emit_event(run_id, {
        "type": "action_resolved",
        "approved": req.approved,
    })
    
    # Возобновляем workflow
    run.status = "running"
    asyncio.create_task(_resume_workflow(run_id))
    
    return {"status": "resumed", "approved": req.approved}


async def _execute_workflow(run_id: str, user_request: str):
    """
    Выполняет LangGraph workflow в фоновой задаче.
    Отправляет SSE-события по мере выполнения узлов.
    """
    print(f"[_execute_workflow] === STARTED for run {run_id} ===")
    
    run = run_manager.get_run(run_id)
    
    try:
        # Начальное состояние
        initial_state = GraphState(
            run_id=run_id,
            user_request=user_request,
        )
        
        # Сохраняем начальное состояние в run
        if run:
            run.graph_state = initial_state.dict()

        # Выполняем граф с потоковой обработкой
        config = {"configurable": {"thread_id": run_id}}
        
        async for event in compiled_graph.astream(
            initial_state.dict(),
            config=config,
            stream_mode="updates",
        ):
            # event — это dict {node_name: state_update}
            for node_name, state_update in event.items():
                # Отправляем node_started
                node_label = NODE_LABELS.get(node_name, node_name)
                await run_manager.emit_event(run_id, {
                    "type": "node_started",
                    "node": node_name,
                    "label": node_label,
                })

                # Специальная обработка для parse_request — отправляем маршрут
                if node_name == "parse_request":
                    intent = state_update.get("intent", "unknown")
                    await run_manager.emit_event(run_id, {
                        "type": "route_detected",
                        "intent": intent,
                        "message": f"Определена задача: {intent}",
                    })

                # Обновляем состояние
                if run and run.graph_state:
                    run.graph_state.update(state_update)

                # Если есть pending_action — отправляем action_pending
                if node_name == "confirm_order" and "pending_action" in state_update:
                    pending_action = state_update["pending_action"]
                    print(f"[DEBUG] Found pending_action in {node_name}: {pending_action}")
                    if pending_action and run:
                        run.pending_action = pending_action
                        print(f"[DEBUG] Sending action_pending event")
                        await run_manager.emit_event(run_id, {
                            "type": "action_pending",
                            "action": pending_action,
                        })
                        print(f"[DEBUG] action_pending event sent")

                # Если есть ответ — отправляем assistant_message
                if "answer" in state_update and state_update["answer"]:
                    await run_manager.emit_event(run_id, {
                        "type": "assistant_message",
                        "content": state_update["answer"],
                    })

                # Отправляем node_finished
                await run_manager.emit_event(run_id, {
                    "type": "node_finished",
                    "node": node_name,
                    "label": node_label,
                })
        
        # Проверяем, есть ли interrupt (ожидание подтверждения)
        state_snapshot = await compiled_graph.aget_state(config)
        
        if state_snapshot.next:
            # Есть следующие узлы — значит graph остановлен на interrupt
            print(f"[_execute_workflow] Graph interrupted, waiting for approval")
            
            # Получаем pending_action из состояния графа
            graph_state = state_snapshot.values
            pending_action = graph_state.get("pending_action") if graph_state else None
            
            print(f"[_execute_workflow] pending_action from graph state: {pending_action}")
            
            if run:
                run.status = "waiting_approval"
                
                if pending_action:
                    # Сохраняем pending_action в run
                    run.pending_action = pending_action
                    
                    # Отправляем action_pending с данными действия
                    await run_manager.emit_event(run_id, {
                        "type": "action_pending",
                        "action": pending_action,
                    })
                    print(f"[_execute_workflow] ✓ Action pending event sent: {pending_action}")
                else:
                    # Fallback если нет pending_action
                    await run_manager.emit_event(run_id, {
                        "type": "waiting_approval",
                        "message": "Ожидается подтверждение действия",
                    })
                    print(f"[_execute_workflow] ⚠ No pending_action found, sent waiting_approval")
            return
        
        # Если нет interrupt — проверяем ошибки и завершаем
        final_state = run.graph_state if run else {}
        errors = final_state.get("errors", [])
        
        if errors:
            await run_manager.emit_event(run_id, {
                "type": "error",
                "message": "; ".join(errors),
            })
            if run:
                run.status = "error"
        else:
            # Успешное завершение
            await run_manager.emit_event(run_id, {
                "type": "run_finished",
                "answer": final_state.get("answer", ""),
            })
            if run:
                run.status = "finished"

    except Exception as e:
        # Глобальная обработка ошибок
        print(f"[_execute_workflow] ERROR: {e}")
        import traceback
        traceback.print_exc()
        await run_manager.emit_event(run_id, {
            "type": "error",
            "message": f"Workflow error: {str(e)}",
        })
        if run:
            run.status = "error"
    
    print(f"[_execute_workflow] === FINISHED for run {run_id} ===")


async def _resume_workflow(run_id: str):
    """
    Возобновляет workflow после подтверждения/отклонения действия.
    """
    print(f"[_resume_workflow] === RESUMING for run {run_id} ===")
    
    run = run_manager.get_run(run_id)
    if not run:
        print(f"[_resume_workflow] Run not found: {run_id}")
        return
    
    try:
        config = {"configurable": {"thread_id": run_id}}
        
        # Получаем текущее состояние графа
        state_snapshot = await compiled_graph.aget_state(config)
        graph_state = state_snapshot.values
        
        # Получаем action_approved из run.pending_action
        action_approved = False
        if run.pending_action:
            action_approved = run.pending_action.get("approved", False)
        
        print(f"[_resume_workflow] action_approved: {action_approved}")
        
        # Обновляем state с action_approved
        await compiled_graph.aupdate_state(
            config,
            {"action_approved": action_approved}
        )
        
        # Продолжаем выполнение
        async for event in compiled_graph.astream(
            None,  # Продолжаем с текущего состояния
            config=config,
            stream_mode="updates",
        ):
            for node_name, state_update in event.items():
                node_label = NODE_LABELS.get(node_name, node_name)
                
                await run_manager.emit_event(run_id, {
                    "type": "node_started",
                    "node": node_name,
                    "label": node_label,
                })
                
                # Обновляем состояние
                if run.graph_state:
                    run.graph_state.update(state_update)
                
                # Если есть ответ — отправляем assistant_message
                if "answer" in state_update and state_update["answer"]:
                    await run_manager.emit_event(run_id, {
                        "type": "assistant_message",
                        "content": state_update["answer"],
                    })
                
                await run_manager.emit_event(run_id, {
                    "type": "node_finished",
                    "node": node_name,
                    "label": node_label,
                })
        
        # Завершаем
        final_state = run.graph_state or {}
        errors = final_state.get("errors", [])
        
        if errors:
            await run_manager.emit_event(run_id, {
                "type": "error",
                "message": "; ".join(errors),
            })
            run.status = "error"
        else:
            await run_manager.emit_event(run_id, {
                "type": "run_finished",
                "answer": final_state.get("answer", ""),
            })
            run.status = "finished"
    
    except Exception as e:
        print(f"[_resume_workflow] ERROR: {e}")
        import traceback
        traceback.print_exc()
        await run_manager.emit_event(run_id, {
            "type": "error",
            "message": f"Resume error: {str(e)}",
        })
        if run:
            run.status = "error"
    
    print(f"[_resume_workflow] === FINISHED for run {run_id} ===")


@router.get("/run/{run_id}/events")
async def stream_events(run_id: str):
    """
    GET /api/run/{run_id}/events
    SSE endpoint — поток событий выполнения.
    """
    run = run_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    async def event_generator():
        print(f"[SSE] Starting event stream for run {run_id}")
        async for event in run_manager.event_stream(run_id):
            # Формат SSE: data: {json}\n\n
            event_json = f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            print(f"[SSE] Sending event: {event.get('type')}")
            yield event_json
        print(f"[SSE] Event stream finished for run {run_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

### 1.22. Backend: main.py

Создай файл `backend/main.py`:

```python
"""
Главный файл FastAPI приложения.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.mcp_server.items_service import get_items_service
from backend.mcp_server.suppliers_service import get_suppliers_service

app = FastAPI(
    title="AI-оператор склада канцелярии",
    version="0.8.0",
    description="Backend для AI-оператора склада на базе LangGraph + OpenAI + MCP",
)

# CORS — разрешаем запросы с frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения."""
    # Инициализируем ItemsService
    items_service = get_items_service()
    print("[Startup] ItemsService initialized")
    print(f"[Startup] Items file: {items_service.file_path}")
    
    # Инициализируем SuppliersService
    suppliers_service = get_suppliers_service()
    print("[Startup] SuppliersService initialized")
    print(f"[Startup] Suppliers file: {suppliers_service.file_path}")
    
    # Инициализируем MCP-клиент
    from backend.mcp_client.client import get_mcp_client
    
    mcp_client = get_mcp_client()
    print(f"[Startup] MCP Client initialized (URL: {mcp_client.server_url})")
    
    # Пробуем получить список инструментов
    try:
        tools_info = mcp_client.list_tools()
        if isinstance(tools_info, dict):
            tools = tools_info.get("tools", [])
            if not tools and "result" in tools_info:
                import json
                try:
                    parsed = json.loads(tools_info["result"])
                    tools = parsed.get("tools", [])
                except:
                    tools = []
        else:
            tools = []
        
        print(f"[Startup] Available MCP tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
    except Exception as e:
        print(f"[Startup] Warning: Could not connect to MCP Server: {e}")
        print(f"[Startup] Make sure MCP Server is running at {mcp_client.server_url}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
```

### 1.23. Backend: mcp_server/schemas.py

Создай файл `backend/mcp_server/schemas.py`:

```python
"""
Схемы данных для MCP-сервера.
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class ItemData(BaseModel):
    """Данные одного товара."""
    item_id: str
    product_name: str
    category: str
    quantity: int
    min_stock: int
    supplier_id: str
    last_ordered: Optional[str] = None
    reorder_date: Optional[str] = None
    unit_price: float = 0
    unit_of_measure: str = ""
    weight_kg: float = 0
    volume_m3: float = 0
    location: str = ""
    expiry_date: Optional[str] = None
    status: str = ""
    ai_status: Optional[str] = None


class SupplierData(BaseModel):
    """Данные одного поставщика."""
    supplier_id: str
    company_name: str
    contact_person: str = ""
    phone: str = ""
    email: str = ""
    contract_start: Optional[str] = None
    contract_end: Optional[str] = None
    payment_terms: str = ""
    rating: float = 0
    last_contact: Optional[str] = None
    status: str = ""


class GetItemsOutput(BaseModel):
    """Результат get_items."""
    success: bool
    items: List[ItemData] = []
    count: int = 0
    error: Optional[str] = None
    error_code: Optional[str] = None


class GetItemOutput(BaseModel):
    """Результат get_item."""
    success: bool
    item: Optional[ItemData] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


class UpdateMinStockOutput(BaseModel):
    """Результат update_min_stock."""
    success: bool
    item_id: Optional[str] = None
    changes: Optional[Dict[str, Dict[str, Any]]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


class GetSuppliersOutput(BaseModel):
    """Результат get_suppliers."""
    success: bool
    suppliers: List[SupplierData] = []
    count: int = 0
    error: Optional[str] = None
    error_code: Optional[str] = None
```

### 1.24. Backend: mcp_server/validation.py

Создай файл `backend/mcp_server/validation.py`:

```python
"""
Валидация данных для MCP-сервера.
"""


def validate_item_id(item_id: str) -> tuple[bool, str]:
    """Проверить формат item_id."""
    if not item_id or not isinstance(item_id, str):
        return False, "item_id должен быть непустой строкой"
    if len(item_id) > 100:
        return False, "item_id слишком длинный"
    return True, ""


def validate_supplier_id(supplier_id: str) -> tuple[bool, str]:
    """Проверить формат supplier_id."""
    if not supplier_id or not isinstance(supplier_id, str):
        return False, "supplier_id должен быть непустой строкой"
    if len(supplier_id) > 100:
        return False, "supplier_id слишком длинный"
    return True, ""


def validate_quantity(value) -> tuple[bool, str]:
    """Проверить что значение количества — целое число >= 0."""
    try:
        qty = int(value)
        if qty < 0:
            return False, f"Количество не может быть отрицательным: {value}"
        return True, ""
    except (ValueError, TypeError):
        return False, f"Некорректное значение количества: {value}"


def validate_min_stock(value) -> tuple[bool, str]:
    """Проверить что значение минимального остатка — целое число >= 0."""
    try:
        min_stock = int(value)
        if min_stock < 0:
            return False, f"Минимальный остаток не может быть отрицательным: {value}"
        return True, ""
    except (ValueError, TypeError):
        return False, f"Некорректное значение минимального остатка: {value}"
```

### 1.25. Backend: mcp_server/items_service.py

Создай файл `backend/mcp_server/items_service.py`:

```python
"""
Сервис для работы с товарами из Excel-таблицы.
"""
import os
from pathlib import Path
from typing import Optional, List
from openpyxl import load_workbook

from backend.mcp_server.schemas import (
    ItemData,
    GetItemsOutput,
    GetItemOutput,
    UpdateMinStockOutput,
)
from backend.mcp_server.validation import (
    validate_item_id,
    validate_min_stock,
)


# Путь к Excel-файлу товаров
ITEMS_FILE_PATH = os.getenv(
    "ITEMS_FILE_PATH",
    str(Path(__file__).parent.parent.parent / "data" / "items.xlsx")
)


class ItemsServiceError(Exception):
    """Ошибка Items-сервиса."""
    def __init__(self, message: str, error_code: str = "ITEMS_ERROR"):
        super().__init__(message)
        self.error_code = error_code


class ItemsService:
    """
    Сервис для работы с товарами из Excel-таблицы.
    """
    
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = Path(file_path or ITEMS_FILE_PATH)
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Проверяет существование файла товаров."""
        if not self.file_path.exists():
            raise ItemsServiceError(
                f"Файл товаров не найден: {self.file_path}. "
                f"Создайте файл или укажите правильный путь в ITEMS_FILE_PATH.",
                error_code="FILE_NOT_FOUND"
            )
    
    def _load_workbook(self, data_only: bool = True):
        """Загружает workbook с обработкой ошибок."""
        try:
            return load_workbook(self.file_path, data_only=data_only)
        except Exception as e:
            raise ItemsServiceError(
                f"Не удалось открыть файл: {e}",
                error_code="FILE_READ_ERROR"
            )
    
    def _get_headers(self, ws) -> List[str]:
        """Получает заголовки из первой строки."""
        return [cell.value for cell in ws[1] if cell.value]
    
    def _find_item_row(self, ws, item_id: str) -> Optional[int]:
        """Находит номер строки товара по item_id."""
        headers = self._get_headers(ws)
        try:
            id_col_idx = headers.index("item_id") + 1
        except ValueError:
            raise ItemsServiceError(
                "Колонка 'item_id' не найдена в таблице",
                error_code="INVALID_SCHEMA"
            )
        
        for row_idx in range(2, ws.max_row + 1):
            if ws.cell(row=row_idx, column=id_col_idx).value == item_id:
                return row_idx
        return None
    
    def _row_to_item_data(self, ws, row_idx: int, headers: List[str]) -> ItemData:
        """Преобразует строку Excel в ItemData."""
        row_data = {}
        for col_idx, header in enumerate(headers, 1):
            value = ws.cell(row=row_idx, column=col_idx).value
            row_data[header] = value if value is not None else ""
        
        # Приводим числовые поля
        try:
            quantity = int(row_data.get("quantity", 0) or 0)
        except (ValueError, TypeError):
            quantity = 0
        
        try:
            min_stock = int(row_data.get("min_stock", 0) or 0)
        except (ValueError, TypeError):
            min_stock = 0
        
        try:
            unit_price = float(row_data.get("unit_price", 0) or 0)
        except (ValueError, TypeError):
            unit_price = 0
        
        try:
            weight_kg = float(row_data.get("weight_kg", 0) or 0)
        except (ValueError, TypeError):
            weight_kg = 0
        
        try:
            volume_m3 = float(row_data.get("volume_m3", 0) or 0)
        except (ValueError, TypeError):
            volume_m3 = 0
        
        return ItemData(
            item_id=str(row_data.get("item_id", "")),
            product_name=str(row_data.get("product_name", "")),
            category=str(row_data.get("category", "")),
            quantity=quantity,
            min_stock=min_stock,
            supplier_id=str(row_data.get("supplier_id", "")),
            last_ordered=str(row_data.get("last_ordered", "") or ""),
            reorder_date=str(row_data.get("reorder_date", "") or ""),
            unit_price=unit_price,
            unit_of_measure=str(row_data.get("unit_of_measure", "")),
            weight_kg=weight_kg,
            volume_m3=volume_m3,
            location=str(row_data.get("location", "")),
            expiry_date=str(row_data.get("expiry_date", "") or ""),
            status=str(row_data.get("status", "")),
            ai_status=str(row_data.get("ai_status", "") or ""),
        )
    
    def get_items(self, item_id: Optional[str] = None, category: Optional[str] = None) -> GetItemsOutput:
        """
        Получить список товаров.
        
        Args:
            item_id: ID товара (если указан — вернуть только этот товар)
            category: Фильтр по категории
        
        Returns:
            GetItemsOutput с списком товаров
        """
        print(f"[ItemsService] get_items(item_id={item_id}, category={category})")
        
        try:
            wb = self._load_workbook()
            ws = wb.active
            headers = self._get_headers(ws)
            
            items = []
            for row_idx in range(2, ws.max_row + 1):
                item = self._row_to_item_data(ws, row_idx, headers)
                
                # Пропускаем пустые строки
                if not item.item_id:
                    continue
                
                # Фильтр по item_id
                if item_id and item.item_id != item_id:
                    continue
                
                # Фильтр по категории
                if category and item.category != category:
                    continue
                
                items.append(item)
            
            wb.close()
            
            print(f"[ItemsService] get_items: found {len(items)} items")
            return GetItemsOutput(
                success=True,
                items=items,
                count=len(items),
            )
        
        except ItemsServiceError as e:
            print(f"[ItemsService] get_items error: {e}")
            return GetItemsOutput(
                success=False,
                error=str(e),
                error_code=e.error_code,
            )
        except Exception as e:
            print(f"[ItemsService] get_items unexpected error: {e}")
            return GetItemsOutput(
                success=False,
                error=f"Неожиданная ошибка: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )
    
    def get_item(self, item_id: str) -> GetItemOutput:
        """
        Получить данные конкретного товара.
        
        Args:
            item_id: ID товара
        
        Returns:
            GetItemOutput с данными товара
        """
        print(f"[ItemsService] get_item(item_id={item_id})")
        
        # Валидация item_id
        ok, msg = validate_item_id(item_id)
        if not ok:
            return GetItemOutput(
                success=False,
                error=msg,
                error_code="INVALID_INPUT",
            )
        
        try:
            wb = self._load_workbook()
            ws = wb.active
            headers = self._get_headers(ws)
            
            row_idx = self._find_item_row(ws, item_id)
            if not row_idx:
                wb.close()
                return GetItemOutput(
                    success=False,
                    error=f"Товар {item_id} не найден",
                    error_code="ITEM_NOT_FOUND",
                )
            
            item = self._row_to_item_data(ws, row_idx, headers)
            wb.close()
            
            print(f"[ItemsService] get_item: found {item.product_name}")
            return GetItemOutput(
                success=True,
                item=item,
            )
        
        except ItemsServiceError as e:
            return GetItemOutput(
                success=False,
                error=str(e),
                error_code=e.error_code,
            )
        except Exception as e:
            return GetItemOutput(
                success=False,
                error=f"Неожиданная ошибка: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )
    
    def update_min_stock(self, item_id: str, new_min_stock: int) -> UpdateMinStockOutput:
        """
        Изменить минимальный остаток товара.
        
        Args:
            item_id: ID товара
            new_min_stock: Новый минимальный остаток
        
        Returns:
            UpdateMinStockOutput с результатом операции
        """
        print(f"[ItemsService] update_min_stock(item_id={item_id}, new_min_stock={new_min_stock})")
        
        # Валидация входных данных
        ok, msg = validate_item_id(item_id)
        if not ok:
            return UpdateMinStockOutput(
                success=False,
                error=msg,
                error_code="INVALID_INPUT",
            )
        
        ok, msg = validate_min_stock(new_min_stock)
        if not ok:
            return UpdateMinStockOutput(
                success=False,
                error=msg,
                error_code="INVALID_INPUT",
            )
        
        try:
            # Загружаем workbook для записи (data_only=False)
            wb = load_workbook(self.file_path)
            ws = wb.active
            headers = self._get_headers(ws)
            
            # Ищем товар
            row_idx = self._find_item_row(ws, item_id)
            if not row_idx:
                wb.close()
                return UpdateMinStockOutput(
                    success=False,
                    error=f"Товар {item_id} не найден",
                    error_code="ITEM_NOT_FOUND",
                )
            
            # Читаем актуальное значение
            min_stock_col = headers.index("min_stock") + 1
            old_min_stock = ws.cell(row=row_idx, column=min_stock_col).value or 0
            
            # Выполняем изменение
            ws.cell(row=row_idx, column=min_stock_col).value = new_min_stock
            wb.save(self.file_path)
            wb.close()
            
            print(f"[ItemsService] update_min_stock: {old_min_stock} → {new_min_stock}")
            return UpdateMinStockOutput(
                success=True,
                item_id=item_id,
                changes={
                    "min_stock": {
                        "old": int(old_min_stock),
                        "new": new_min_stock,
                    }
                },
                message=f"Минимальный остаток товара {item_id} успешно изменён",
            )
        
        except ItemsServiceError as e:
            return UpdateMinStockOutput(
                success=False,
                error=str(e),
                error_code=e.error_code,
            )
        except Exception as e:
            return UpdateMinStockOutput(
                success=False,
                error=f"Неожиданная ошибка: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )


# Singleton
_items_service: Optional[ItemsService] = None


def get_items_service() -> ItemsService:
    """Получить экземпляр ItemsService."""
    global _items_service
    if _items_service is None:
        _items_service = ItemsService()
    return _items_service
```

### 1.26. Backend: mcp_server/suppliers_service.py

Создай файл `backend/mcp_server/suppliers_service.py`:

```python
"""
Сервис для работы с поставщиками из Excel-таблицы.
"""
import os
from pathlib import Path
from typing import Optional, List
from openpyxl import load_workbook

from backend.mcp_server.schemas import (
    SupplierData,
    GetSuppliersOutput,
)
from backend.mcp_server.validation import validate_supplier_id


# Путь к Excel-файлу поставщиков
SUPPLIERS_FILE_PATH = os.getenv(
    "SUPPLIERS_FILE_PATH",
    str(Path(__file__).parent.parent.parent / "data" / "suppliers.xlsx")
)


class SuppliersServiceError(Exception):
    """Ошибка Suppliers-сервиса."""
    def __init__(self, message: str, error_code: str = "SUPPLIERS_ERROR"):
        super().__init__(message)
        self.error_code = error_code


class SuppliersService:
    """
    Сервис для работы с поставщиками из Excel-таблицы.
    """
    
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = Path(file_path or SUPPLIERS_FILE_PATH)
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Проверяет существование файла поставщиков."""
        if not self.file_path.exists():
            raise SuppliersServiceError(
                f"Файл поставщиков не найден: {self.file_path}. "
                f"Создайте файл или укажите правильный путь в SUPPLIERS_FILE_PATH.",
                error_code="FILE_NOT_FOUND"
            )
    
    def _load_workbook(self, data_only: bool = True):
        """Загружает workbook с обработкой ошибок."""
        try:
            return load_workbook(self.file_path, data_only=data_only)
        except Exception as e:
            raise SuppliersServiceError(
                f"Не удалось открыть файл: {e}",
                error_code="FILE_READ_ERROR"
            )
    
    def _get_headers(self, ws) -> List[str]:
        """Получает заголовки из первой строки."""
        return [cell.value for cell in ws[1] if cell.value]
    
    def _row_to_supplier_data(self, ws, row_idx: int, headers: List[str]) -> SupplierData:
        """Преобразует строку Excel в SupplierData."""
        row_data = {}
        for col_idx, header in enumerate(headers, 1):
            value = ws.cell(row=row_idx, column=col_idx).value
            row_data[header] = value if value is not None else ""
        
        # Приводим числовые поля
        try:
            rating = float(row_data.get("rating", 0) or 0)
        except (ValueError, TypeError):
            rating = 0
        
        return SupplierData(
            supplier_id=str(row_data.get("supplier_id", "")),
            company_name=str(row_data.get("company_name", "")),
            contact_person=str(row_data.get("contact_person", "")),
            phone=str(row_data.get("phone", "")),
            email=str(row_data.get("email", "")),
            contract_start=str(row_data.get("contract_start", "") or ""),
            contract_end=str(row_data.get("contract_end", "") or ""),
            payment_terms=str(row_data.get("payment_terms", "")),
            rating=rating,
            last_contact=str(row_data.get("last_contact", "") or ""),
            status=str(row_data.get("status", "")),
        )
    
    def get_suppliers(self) -> GetSuppliersOutput:
        """
        Получить список всех поставщиков.
        
        Returns:
            GetSuppliersOutput с списком поставщиков
        """
        print(f"[SuppliersService] get_suppliers()")
        
        try:
            wb = self._load_workbook()
            ws = wb.active
            headers = self._get_headers(ws)
            
            suppliers = []
            for row_idx in range(2, ws.max_row + 1):
                supplier = self._row_to_supplier_data(ws, row_idx, headers)
                
                # Пропускаем пустые строки
                if not supplier.supplier_id:
                    continue
                
                suppliers.append(supplier)
            
            wb.close()
            
            print(f"[SuppliersService] get_suppliers: found {len(suppliers)} suppliers")
            return GetSuppliersOutput(
                success=True,
                suppliers=suppliers,
                count=len(suppliers),
            )
        
        except SuppliersServiceError as e:
            print(f"[SuppliersService] get_suppliers error: {e}")
            return GetSuppliersOutput(
                success=False,
                error=str(e),
                error_code=e.error_code,
            )
        except Exception as e:
            print(f"[SuppliersService] get_suppliers unexpected error: {e}")
            return GetSuppliersOutput(
                success=False,
                error=f"Неожиданная ошибка: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )


# Singleton
_suppliers_service: Optional[SuppliersService] = None


def get_suppliers_service() -> SuppliersService:
    """Получить экземпляр SuppliersService."""
    global _suppliers_service
    if _suppliers_service is None:
        _suppliers_service = SuppliersService()
    return _suppliers_service
```

### 1.27. Backend: mcp_server/server.py

Создай файл `backend/mcp_server/server.py`:

```python
"""
MCP Server для работы с Excel-таблицами товаров и поставщиков склада канцелярии.
Использует официальный MCP SDK от Anthropic.

Запуск:
    # Через Python (рекомендуется):
    python backend/mcp_server/server.py
    
    # Или через mcp CLI (порт задаётся через переменную окружения):
    MCP_SERVER_PORT=8001 mcp run backend/mcp_server/server.py --transport streamable-http
"""
import os
import sys
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp.server import MCPServer
from backend.mcp_server.items_service import get_items_service

# Создаём MCP-сервер
mcp = MCPServer("Warehouse Items MCP Server")


@mcp.tool()
def get_items(item_id: str = None, category: str = None) -> dict:
    """
    Получить список товаров из Excel-таблицы склада.
    
    Args:
        item_id: ID товара. Если не указан — вернуть все товары.
        category: Фильтр по категории: Бумага, Письменные принадлежности, и т.д.
    
    Returns:
        Структурированный список товаров.
    """
    service = get_items_service()
    result = service.get_items(item_id=item_id, category=category)
    return result.model_dump()


@mcp.tool()
def get_item(item_id: str) -> dict:
    """
    Получить данные конкретного товара по ID.
    
    Args:
        item_id: ID товара, например 'item_001'
    
    Returns:
        Данные товара или ошибка, если товар не найден.
    """
    service = get_items_service()
    result = service.get_item(item_id)
    return result.model_dump()


@mcp.tool()
def update_min_stock(item_id: str, new_min_stock: int) -> dict:
    """
    Изменить минимальный остаток товара в Excel-таблице.
    
    Args:
        item_id: ID товара
        new_min_stock: Новый минимальный остаток
    
    Returns:
        Результат операции с информацией об изменениях.
    """
    service = get_items_service()
    result = service.update_min_stock(item_id, new_min_stock)
    return result.model_dump()


@mcp.tool()
def get_suppliers() -> dict:
    """
    Получить список поставщиков из Excel-таблицы.
    
    Returns:
        Структурированный список поставщиков.
    """
    from backend.mcp_server.suppliers_service import get_suppliers_service
    service = get_suppliers_service()
    result = service.get_suppliers()
    return result.model_dump()


@mcp.tool()
def list_tools_info() -> dict:
    """
    Получить информацию о доступных инструментах.
    
    Returns:
        Список инструментов с описаниями.
    """
    return {
        "tools": [
            {
                "name": "get_items",
                "description": "Получить список товаров из Excel-таблицы склада",
            },
            {
                "name": "get_item",
                "description": "Получить данные конкретного товара по ID",
            },
            {
                "name": "update_min_stock",
                "description": "Изменить минимальный остаток товара в Excel-таблице",
            },
            {
                "name": "get_suppliers",
                "description": "Получить список поставщиков из Excel-таблицы",
            },
        ]
    }


# Точка входа для запуска как HTTP сервера
if __name__ == "__main__":
    # Получаем порт из переменной окружения или используем 8001
    port = int(os.getenv("MCP_SERVER_PORT", "8001"))
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    
    print(f"[Warehouse MCP Server] Запуск HTTP сервера на {host}:{port}...", file=sys.stderr)
    print(f"[Warehouse MCP Server] URL: http://{host}:{port}", file=sys.stderr)
    
    # Запускаем через mcp.run() с streamable-http транспортом
    mcp.run(
        transport="streamable-http",
        host=host,
        port=port
    )
```

### 1.28. Backend: mcp_client/client.py

Создай файл `backend/mcp_client/client.py`:

```python
"""
MCP Client — обёртка для вызова MCP-инструментов через HTTP.

Использует streamable-http транспорт для связи с MCP-сервером.
MCP-сервер должен быть запущен отдельно на порту 8001.

Архитектура:
  FastAPI (порт 8000)
    └── MCP Client
          └── HTTP запросы → MCP Server (порт 8001)
                └── Excel Services
                      └── Excel-файлы
"""
import os
import asyncio
from typing import Optional, Dict, Any

import httpx


class MCPClientError(Exception):
    """Ошибка MCP-клиента."""
    def __init__(self, message: str, error_code: str = "MCP_CLIENT_ERROR"):
        super().__init__(message)
        self.error_code = error_code


class MCPClient:
    """
    HTTP-клиент для вызова MCP-инструментов.
    Все вызовы к Excel проходят через HTTP к MCP-серверу.
    """
    
    def __init__(self):
        self.server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001/mcp")
    
    def _call_tool_sync(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Вызвать инструмент синхронно через HTTP.
        """
        print(f"[MCPClient] call_tool: {tool_name} (HTTP → {self.server_url})")
        
        try:
            # Формируем JSON-RPC запрос
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments,
                }
            }
            
            # Отправляем HTTP POST запрос
            with httpx.Client() as client:
                response = client.post(
                    self.server_url,
                    json=request,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise MCPClientError(
                        f"HTTP error: {response.status_code}",
                        error_code="HTTP_ERROR"
                    )
                
                result = response.json()
                
                # Извлекаем результат из JSON-RPC ответа
                if "result" in result:
                    return result["result"]
                elif "error" in result:
                    raise MCPClientError(
                        result["error"].get("message", "Unknown error"),
                        error_code="RPC_ERROR"
                    )
                else:
                    return result
                
        except httpx.TimeoutException:
            raise MCPClientError(
                "Timeout while calling MCP tool",
                error_code="TIMEOUT"
            )
        except httpx.HTTPError as e:
            raise MCPClientError(
                f"HTTP error: {str(e)}",
                error_code="HTTP_ERROR"
            )
        except Exception as e:
            raise MCPClientError(
                f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR"
            )
    
    def get_items(self, item_id: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Получить список товаров через MCP.
        
        Args:
            item_id: ID товара (если None — вернуть все)
            category: фильтр по категории
            
        Returns:
            Результат в формате MCP
        """
        print(f"[MCPClient] get_items(item_id={item_id}, category={category})")
        
        arguments = {}
        if item_id is not None:
            arguments["item_id"] = item_id
        if category is not None:
            arguments["category"] = category
        
        try:
            result = self._call_tool_sync("get_items", arguments)
            print(f"[MCPClient] get_items result: success={result.get('success')}, count={result.get('count', 0)}")
            return result
        except Exception as e:
            print(f"[MCPClient] get_items error: {e}")
            return {
                "success": False,
                "error": f"MCP-сервер недоступен: {str(e)}",
                "error_code": "MCP_SERVER_UNAVAILABLE",
                "items": [],
                "count": 0,
            }
    
    def get_item(self, item_id: str) -> Dict[str, Any]:
        """
        Получить данные конкретного товара через MCP.
        
        Args:
            item_id: ID товара
            
        Returns:
            Результат в формате MCP
        """
        print(f"[MCPClient] get_item(item_id={item_id})")
        
        try:
            result = self._call_tool_sync("get_item", {"item_id": item_id})
            print(f"[MCPClient] get_item result: success={result.get('success')}")
            return result
        except Exception as e:
            print(f"[MCPClient] get_item error: {e}")
            return {
                "success": False,
                "error": f"MCP-сервер недоступен: {str(e)}",
                "error_code": "MCP_SERVER_UNAVAILABLE",
                "item": None,
            }
    
    def update_min_stock(self, item_id: str, new_min_stock: int) -> Dict[str, Any]:
        """
        Изменить минимальный остаток товара через MCP.
        
        Args:
            item_id: ID товара
            new_min_stock: новый минимальный остаток
            
        Returns:
            Результат в формате MCP
        """
        print(f"[MCPClient] update_min_stock(item_id={item_id}, new_min_stock={new_min_stock})")
        
        try:
            result = self._call_tool_sync(
                "update_min_stock",
                {"item_id": item_id, "new_min_stock": new_min_stock}
            )
            print(f"[MCPClient] update_min_stock result: success={result.get('success')}")
            return result
        except Exception as e:
            print(f"[MCPClient] update_min_stock error: {e}")
            return {
                "success": False,
                "error": f"MCP-сервер недоступен: {str(e)}",
                "error_code": "MCP_SERVER_UNAVAILABLE",
            }
    
    def get_suppliers(self) -> Dict[str, Any]:
        """
        Получить список поставщиков через MCP.
        
        Returns:
            Результат в формате MCP
        """
        print(f"[MCPClient] get_suppliers()")
        
        try:
            result = self._call_tool_sync("get_suppliers", {})
            print(f"[MCPClient] get_suppliers result: success={result.get('success')}, count={result.get('count', 0)}")
            return result
        except Exception as e:
            print(f"[MCPClient] get_suppliers error: {e}")
            return {
                "success": False,
                "error": f"MCP-сервер недоступен: {str(e)}",
                "error_code": "MCP_SERVER_UNAVAILABLE",
                "suppliers": [],
                "count": 0,
            }
    
    def list_tools(self) -> Dict[str, Any]:
        """Получить список доступных инструментов."""
        try:
            return self._call_tool_sync("list_tools_info", {})
        except Exception as e:
            print(f"[MCPClient] list_tools error: {e}")
            return {"tools": []}


# Singleton
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Получить экземпляр MCP-клиента."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client
```

### 1.29. Frontend: src/types.ts

Создай файл `src/types.ts`:

```typescript
/**
 * Типы событий SSE от backend.
 */
export interface SSEEvent {
  type:
    | "run_started"
    | "node_started"
    | "node_finished"
    | "assistant_message"
    | "tool_started"
    | "tool_finished"
    | "route_detected"
    | "action_pending"
    | "waiting_approval"
    | "action_resolved"
    | "error"
    | "run_finished"
    | "heartbeat";
  run_id?: string;
  node?: string;
  label?: string;
  tool?: string;
  intent?: string;
  content?: string;
  message?: string;
  answer?: string;
  success?: boolean;
  action?: {
    action_type: string;
    target_supplier_id?: string;
    supplier_name?: string;
    items?: any[];
    total_cost?: number;
    description?: string;
  };
  approved?: boolean;
}
```

### 1.30. Frontend: src/components/Header.tsx

Создай файл `src/components/Header.tsx`:

```tsx
export function Header() {
  return (
    <header className="flex items-center gap-3 mb-8">
      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center text-2xl font-bold shadow-lg shadow-emerald-500/20">
        🏪
      </div>
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          AI-оператор склада канцелярии
        </h1>
        <p className="text-sm text-slate-400">
          Интеллектуальное управление складом с AI-анализом
        </p>
      </div>
    </header>
  );
}
```

### 1.31. Frontend: src/components/RunInput.tsx

Создай файл `src/components/RunInput.tsx`:

```tsx
interface RunInputProps {
  value: string;
  onChange: (value: string) => void;
  onRun: () => void;
  onStop: () => void;
  isRunning: boolean;
}

export function RunInput({
  value,
  onChange,
  onRun,
  onStop,
  isRunning,
}: RunInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onRun();
    }
  };

  return (
    <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-2xl p-4 shadow-xl">
      <label className="block text-sm font-medium text-slate-300 mb-2">
        Опишите задачу
      </label>
      <div className="flex gap-3">
        <textarea
          className="flex-1 bg-slate-900/80 border border-slate-600/50 rounded-xl px-4 py-3 text-white placeholder-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all"
          rows={2}
          placeholder="Например: проанализируй товары с дефицитом..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isRunning}
        />
        <div className="flex flex-col gap-2">
          {!isRunning ? (
            <button
              onClick={onRun}
              disabled={!value.trim()}
              className="px-5 py-3 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/20 transition-all duration-200 flex items-center gap-2 whitespace-nowrap"
            >
              <span>▶</span> Запустить
            </button>
          ) : (
            <button
              onClick={onStop}
              className="px-5 py-3 bg-red-600 hover:bg-red-500 text-white font-semibold rounded-xl shadow-lg transition-all duration-200 flex items-center gap-2 whitespace-nowrap"
            >
              <span>⏹</span> Стоп
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
```

### 1.32. Frontend: src/components/AnswerPanel.tsx

Создай файл `src/components/AnswerPanel.tsx`:

```tsx
interface AnswerPanelProps {
  answer: string;
  isRunning: boolean;
}

export function AnswerPanel({ answer, isRunning }: AnswerPanelProps) {
  return (
    <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-2xl p-5 shadow-xl flex-1 min-h-[200px]">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">💬</span>
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Ответ AI
        </h2>
        {isRunning && (
          <span className="ml-auto flex items-center gap-1.5 text-xs text-emerald-400">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
            Обработка...
          </span>
        )}
      </div>

      <div className="text-slate-100 leading-relaxed whitespace-pre-wrap">
        {answer ? (
          <div className="animate-fade-in">{answer}</div>
        ) : isRunning ? (
          <div className="flex items-center gap-2 text-slate-500">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
            <span className="text-sm">AI анализирует...</span>
          </div>
        ) : (
          <div className="text-slate-500 text-sm italic">
            Здесь появится ответ AI после выполнения запроса
          </div>
        )}
      </div>
    </div>
  );
}
```

### 1.33. Frontend: src/components/ExecutionLog.tsx

Создай файл `src/components/ExecutionLog.tsx`:

```tsx
import type { SSEEvent } from "../types";

interface ExecutionLogProps {
  events: SSEEvent[];
}

function getEventIcon(type: string, tool?: string): string {
  switch (type) {
    case "run_started":
      return "🚀";
    case "node_started":
      return "⏳";
    case "node_finished":
      return "✅";
    case "assistant_message":
      return "💬";
    case "tool_started":
      return "🔧";
    case "tool_finished":
      return "🔧";
    case "route_detected":
      return "🔀";
    case "action_pending":
      return "⚠️";
    case "waiting_approval":
      return "⏸️";
    case "action_resolved":
      return "✓";
    case "error":
      return "❌";
    case "run_finished":
      return "🏁";
    case "heartbeat":
      return "💓";
    default:
      return "📌";
  }
}

function getEventLabel(event: SSEEvent): string {
  switch (event.type) {
    case "run_started":
      return "Запуск workflow";
    case "node_started":
      return event.label ? `${event.label}...` : `Узел: ${event.node}`;
    case "node_finished":
      return event.label ? `✓ ${event.label}` : `Завершён: ${event.node}`;
    case "assistant_message":
      return "Ответ LLM";
    case "tool_started":
      return `MCP: ${event.tool} — выполнение...`;
    case "tool_finished": {
      const status = event.success ? "✓" : "✗";
      const msg = event.message || "";
      return `${event.tool}: ${status} ${msg}`;
    }
    case "route_detected":
      return `🔀 Маршрут: ${event.intent}`;
    case "action_pending":
      return `⚠️ Ожидается подтверждение действия`;
    case "waiting_approval":
      return `⏸️ ${event.message || "Ожидание подтверждения"}`;
    case "action_resolved":
      return event.approved ? `✓ Действие подтверждено` : `✗ Действие отклонено`;
    case "error":
      return `Ошибка: ${event.message}`;
    case "run_finished":
      return "Выполнение завершено";
    case "heartbeat":
      return "Heartbeat";
    default:
      return event.type;
  }
}

function getEventColor(type: string, success?: boolean): string {
  switch (type) {
    case "run_started":
      return "text-blue-400";
    case "node_started":
      return "text-yellow-400";
    case "node_finished":
      return "text-emerald-400";
    case "assistant_message":
      return "text-purple-400";
    case "tool_started":
      return "text-cyan-400";
    case "tool_finished":
      return success ? "text-emerald-400" : "text-red-400";
    case "route_detected":
      return "text-orange-400";
    case "action_pending":
      return "text-amber-400";
    case "waiting_approval":
      return "text-amber-400";
    case "action_resolved":
      return success ? "text-emerald-400" : "text-red-400";
    case "error":
      return "text-red-400";
    case "run_finished":
      return "text-emerald-400";
    default:
      return "text-slate-400";
  }
}

export function ExecutionLog({ events }: ExecutionLogProps) {
  // Фильтруем heartbeat из отображения
  const displayEvents = events.filter((e) => e.type !== "heartbeat");

  return (
    <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-2xl p-5 shadow-xl">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">📋</span>
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Выполнение
        </h2>
        {displayEvents.length > 0 && (
          <span className="ml-auto text-xs text-slate-500">
            {displayEvents.length} событий
          </span>
        )}
      </div>

      <div className="space-y-1.5 max-h-[300px] overflow-y-auto">
        {displayEvents.length === 0 ? (
          <div className="text-slate-500 text-sm italic py-4 text-center">
            Журнал пуст — запустите задачу для отслеживания выполнения
          </div>
        ) : (
          displayEvents.map((event, index) => (
            <div
              key={index}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/40 text-sm ${getEventColor(event.type, event.success)}`}
            >
              <span className="text-xs">
                {getEventIcon(event.type, event.tool)}
              </span>
              <span className="font-mono text-xs opacity-60">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span className="flex-1 truncate">{getEventLabel(event)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
```

### 1.34. Frontend: src/components/ActionApproval.tsx

Создай файл `src/components/ActionApproval.tsx`:

```tsx
import type { SSEEvent } from "../types";

interface ActionApprovalProps {
  action: SSEEvent["action"];
  onApprove: () => void;
  onReject: () => void;
}

export function ActionApproval({ action, onApprove, onReject }: ActionApprovalProps) {
  if (!action) return null;

  const actionLabels: Record<string, string> = {
    create_order: "Создание заказа",
  };

  return (
    <div className="bg-amber-900/40 border border-amber-500/50 rounded-xl p-5 shadow-xl">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-2xl">⚠️</span>
        <h3 className="text-lg font-semibold text-amber-200">
          Требуется подтверждение
        </h3>
      </div>

      <div className="bg-slate-900/60 rounded-lg p-4 mb-4 space-y-2">
        <div className="flex justify-between">
          <span className="text-slate-400">Действие:</span>
          <span className="text-white font-medium">
            {actionLabels[action.action_type] || action.action_type}
          </span>
        </div>

        {action.supplier_name && (
          <div className="flex justify-between">
            <span className="text-slate-400">Поставщик:</span>
            <span className="text-white">{action.supplier_name}</span>
          </div>
        )}

        {action.items && action.items.length > 0 && (
          <div className="mt-2 pt-2 border-t border-slate-700">
            <span className="text-slate-400 text-sm block mb-2">Товары:</span>
            <div className="space-y-1">
              {action.items.map((item, idx) => (
                <div key={idx} className="text-sm text-slate-300">
                  • {item.product_name} — {item.quantity} {item.unit_of_measure || "шт"} × {item.unit_price} руб.
                </div>
              ))}
            </div>
          </div>
        )}

        {action.total_cost && (
          <div className="flex justify-between mt-2 pt-2 border-t border-slate-700">
            <span className="text-slate-400 font-semibold">Общая стоимость:</span>
            <span className="text-emerald-400 font-bold">{action.total_cost.toFixed(2)} руб.</span>
          </div>
        )}

        {action.description && (
          <div className="mt-2 pt-2 border-t border-slate-700">
            <span className="text-slate-400 text-sm">{action.description}</span>
          </div>
        )}
      </div>

      <div className="flex gap-3">
        <button
          onClick={onApprove}
          className="flex-1 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
        >
          <span>✓</span> Подтвердить
        </button>
        <button
          onClick={onReject}
          className="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-500 text-white font-semibold rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
        >
          <span>✗</span> Отклонить
        </button>
      </div>
    </div>
  );
}
```

### 1.35. Frontend: src/App.tsx

Создай файл `src/App.tsx`:

```tsx
import { useState, useEffect, useRef } from 'react';
import { RunInput } from './components/RunInput';
import { AnswerPanel } from './components/AnswerPanel';
import { ExecutionLog } from './components/ExecutionLog';
import { ActionApproval } from './components/ActionApproval';
import type { SSEEvent } from './types';

export default function App() {
  const [request, setRequest] = useState('');
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [answer, setAnswer] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [pendingAction, setPendingAction] = useState<any>(null);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const handleRun = async () => {
    if (!request.trim() || isRunning) return;

    setIsRunning(true);
    setEvents([]);
    setAnswer('');
    setPendingAction(null);

    try {
      // Создаём запуск
      const response = await fetch('http://localhost:8000/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request: request.trim() }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const { run_id } = await response.json();
      setCurrentRunId(run_id);

      // Подключаемся к SSE
      const eventSource = new EventSource(`http://localhost:8000/api/run/${run_id}/events`);
      eventSourceRef.current = eventSource;

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setEvents((prev) => [...prev, data]);

          // Обрабатываем разные типы событий
          if (data.type === 'assistant_message' && data.content) {
            setAnswer(data.content);
          }

          if (data.type === 'action_pending' && data.action) {
            setPendingAction(data.action);
          }

          if (data.type === 'run_finished') {
            setIsRunning(false);
            eventSource.close();
          }

          if (data.type === 'error') {
            setIsRunning(false);
            setAnswer(`Ошибка: ${data.message}`);
            eventSource.close();
          }
        } catch (error) {
          console.error('Error parsing SSE event:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        setIsRunning(false);
        eventSource.close();
      };
    } catch (error) {
      console.error('Error starting run:', error);
      setIsRunning(false);
      setAnswer(`Ошибка запуска: ${error}`);
    }
  };

  const handleStop = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    setIsRunning(false);
  };

  const handleApprove = async (approved: boolean) => {
    if (!currentRunId) return;

    try {
      const response = await fetch(`http://localhost:8000/api/run/${currentRunId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setPendingAction(null);
    } catch (error) {
      console.error('Error approving action:', error);
    }
  };

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-center mb-2">
            🏪 AI-оператор склада канцелярии
          </h1>
          <p className="text-center text-slate-400">
            Интеллектуальное управление складом с AI-анализом
          </p>
        </header>

        <main className="max-w-6xl mx-auto space-y-6">
          <RunInput
            value={request}
            onChange={setRequest}
            onRun={handleRun}
            onStop={handleStop}
            isRunning={isRunning}
          />

          {pendingAction && (
            <ActionApproval
              action={pendingAction}
              onApprove={() => handleApprove(true)}
              onReject={() => handleApprove(false)}
            />
          )}

          <AnswerPanel answer={answer} isRunning={isRunning} />

          <ExecutionLog events={events} />
        </main>

        <footer className="mt-12 text-center text-slate-500 text-sm">
          <p>AI-оператор склада канцелярии v0.8.0</p>
        </footer>
      </div>
    </div>
  );
}
```

### 1.36. Frontend: src/main.tsx

Создай файл `src/main.tsx`:

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

### 1.37. Frontend: src/index.css

Создай файл `src/index.css`:

```css
@import "tailwindcss";

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.3s ease-out;
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.4);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(100, 116, 139, 0.6);
}
```

### 1.38. Frontend: index.html

Создай файл `index.html`:

```html
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AI-оператор склада канцелярии</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### 1.39. Frontend: package.json

Создай файл `package.json`:

```json
{
  "name": "ai-warehouse-operator",
  "private": true,
  "version": "0.8.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@eslint/js": "^9.17.0",
    "@types/react": "^18.3.18",
    "@types/react-dom": "^18.3.5",
    "@vitejs/plugin-react": "^4.3.4",
    "eslint": "^9.17.0",
    "eslint-plugin-react-hooks": "^5.0.0",
    "eslint-plugin-react-refresh": "^0.4.16",
    "globals": "^15.14.0",
    "typescript": "~5.6.2",
    "typescript-eslint": "^8.18.2",
    "vite": "^6.0.5",
    "@tailwindcss/vite": "^4.0.0",
    "tailwindcss": "^4.0.0"
  }
}
```

### 1.40. Frontend: tsconfig.json

Создай файл `tsconfig.json`:

```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true
  },
  "include": ["src"]
}
```

### 1.41. Frontend: vite.config.ts

Создай файл `vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 3000,
  },
})
```

---

## ЭТАП 2: СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ

### 2.1. Создание Excel-файлов

Создай Python-скрипт `backend/scripts/generate_test_data.py`:

```python
"""
Скрипт для генерации тестовых данных: Excel-файлы товаров и поставщиков.
"""
import os
from pathlib import Path
from openpyxl import Workbook
from openpyxl.utils import get_column_letter


def create_items_excel():
    """Создаёт Excel-файл с товарами."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Товары"
    
    # Заголовки
    headers = [
        "item_id", "product_name", "category", "quantity", "min_stock",
        "supplier_id", "last_ordered", "reorder_date", "unit_price",
        "unit_of_measure", "weight_kg", "volume_m3", "location",
        "expiry_date", "status", "ai_status"
    ]
    ws.append(headers)
    
    # Данные товаров (60 позиций канцелярии)
    items_data = [
        # Бумага (10 товаров)
        ["item_001", "Бумага офисная А4 80г/м²", "Бумага", 45, 50, "supplier_001", "2026-08-25", "2026-09-25", 350, "пачка", 2.5, 0.015, "Склад А", "", "active", ""],
        ["item_002", "Бумага офисная А3 80г/м²", "Бумага", 12, 20, "supplier_003", "2026-08-20", "2026-09-20", 650, "пачка", 5.0, 0.03, "Склад А", "", "active", ""],
        ["item_003", "Бумага цветная А4 (набор 10 цветов)", "Бумага", 8, 15, "supplier_003", "2026-08-15", "2026-09-15", 450, "набор", 3.0, 0.02, "Склад А", "", "active", ""],
        ["item_004", "Бумага фотобумага А4 200г/м²", "Бумага", 5, 10, "supplier_003", "2026-08-10", "2026-09-10", 800, "пачка", 2.0, 0.015, "Склад А", "", "active", ""],
        ["item_005", "Бумага самоклеящаяся А4", "Бумага", 25, 20, "supplier_001", "2026-09-01", "2026-10-01", 280, "пачка", 1.5, 0.01, "Склад А", "", "active", ""],
        ["item_006", "Бумага миллиметровая А3", "Бумага", 3, 10, "supplier_003", "2026-05-01", "2026-06-01", 420, "рулон", 4.0, 0.025, "Склад А", "", "active", ""],
        ["item_007", "Бумага копировальная А4", "Бумага", 15, 10, "supplier_001", "2026-08-28", "2026-09-28", 320, "пачка", 1.8, 0.012, "Склад А", "", "active", ""],
        ["item_008", "Бумага для факса А4", "Бумага", 0, 15, "supplier_001", "2026-05-10", "2026-06-10", 250, "рулон", 1.2, 0.008, "Склад А", "", "active", ""],
        ["item_009", "Бумага чертежная А1", "Бумага", 2, 5, "supplier_003", "2026-05-15", "2026-06-15", 950, "рулон", 6.0, 0.04, "Склад А", "", "active", ""],
        ["item_010", "Бумага офисная А4 70г/м² (эконом)", "Бумага", 60, 40, "supplier_001", "2026-09-05", "2026-10-05", 280, "пачка", 2.3, 0.014, "Склад А", "", "active", ""],
        
        # Письменные принадлежности (10 товаров)
        ["item_011", "Ручка шариковая синяя", "Письменные принадлежности", 150, 100, "supplier_001", "2026-08-20", "2026-09-20", 25, "шт", 0.01, 0.0001, "Склад Б", "", "active", ""],
        ["item_012", "Ручка шариковая черная", "Письменные принадлежности", 80, 100, "supplier_001", "2026-08-18", "2026-09-18", 25, "шт", 0.01, 0.0001, "Склад Б", "", "active", ""],
        ["item_013", "Ручка гелевая синяя", "Письменные принадлежности", 45, 50, "supplier_004", "2026-08-25", "2026-09-25", 45, "шт", 0.015, 0.0001, "Склад Б", "", "active", ""],
        ["item_014", "Карандаш простой HB", "Письменные принадлежности", 120, 80, "supplier_001", "2026-09-01", "2026-10-01", 18, "шт", 0.005, 0.00005, "Склад Б", "", "active", ""],
        ["item_015", "Карандаш цветной (набор 12 шт)", "Письменные принадлежности", 15, 20, "supplier_004", "2026-08-10", "2026-09-10", 180, "набор", 0.15, 0.001, "Склад Б", "", "active", ""],
        ["item_016", "Маркер перманентный черный", "Письменные принадлежности", 35, 30, "supplier_001", "2026-08-22", "2026-09-22", 65, "шт", 0.02, 0.0002, "Склад Б", "", "active", ""],
        ["item_017", "Маркер на водной основе (набор 10 шт)", "Письменные принадлежности", 8, 15, "supplier_004", "2026-04-15", "2026-05-15", 280, "набор", 0.25, 0.002, "Склад Б", "", "active", ""],
        ["item_018", "Ручка капиллярная черная", "Письменные принадлежности", 25, 30, "supplier_001", "2026-08-30", "2026-09-30", 55, "шт", 0.012, 0.0001, "Склад Б", "", "active", ""],
        ["item_019", "Линтер для ручек", "Письменные принадлежности", 40, 25, "supplier_004", "2026-08-15", "2026-09-15", 35, "шт", 0.008, 0.0001, "Склад Б", "", "active", ""],
        ["item_020", "Набор для черчения (5 предметов)", "Письменные принадлежности", 6, 10, "supplier_004", "2026-03-20", "2026-04-20", 450, "набор", 0.35, 0.003, "Склад Б", "", "active", ""],
        
        # Тетради и блокноты (10 товаров)
        ["item_021", "Тетрадь 48 листов клетка", "Тетради и блокноты", 200, 150, "supplier_002", "2026-08-28", "2026-09-28", 45, "шт", 0.12, 0.001, "Склад В", "", "active", ""],
        ["item_022", "Тетрадь 96 листов линия", "Тетради и блокноты", 85, 100, "supplier_002", "2026-08-20", "2026-09-20", 75, "шт", 0.22, 0.002, "Склад В", "", "active", ""],
        ["item_023", "Тетрадь общая 96 листов", "Тетради и блокноты", 60, 80, "supplier_002", "2026-08-25", "2026-09-25", 95, "шт", 0.25, 0.002, "Склад В", "", "active", ""],
        ["item_024", "Блокнот А5 в клетку", "Тетради и блокноты", 35, 40, "supplier_002", "2026-08-22", "2026-09-22", 120, "шт", 0.18, 0.0015, "Склад В", "", "active", ""],
        ["item_025", "Блокнот А4 в линейку", "Тетради и блокноты", 20, 30, "supplier_002", "2026-08-15", "2026-09-15", 150, "шт", 0.28, 0.0025, "Склад В", "", "active", ""],
        ["item_026", "Ежедневник датированный 2027", "Тетради и блокноты", 45, 50, "supplier_002", "2026-08-28", "2026-09-28", 350, "шт", 0.35, 0.003, "Склад В", "", "active", ""],
        ["item_027", "Ежедневник недатированный", "Тетради и блокноты", 18, 25, "supplier_002", "2026-08-10", "2026-09-10", 280, "шт", 0.3, 0.0025, "Склад В", "", "active", ""],
        ["item_028", "Блок для заметок А6 (100 листов)", "Тетради и блокноты", 50, 40, "supplier_004", "2026-09-02", "2026-10-02", 85, "блок", 0.15, 0.001, "Склад В", "", "active", ""],
        ["item_029", "Тетрадь для нот А4", "Тетради и блокноты", 12, 15, "supplier_002", "2026-05-20", "2026-06-20", 110, "шт", 0.2, 0.002, "Склад В", "", "active", ""],
        ["item_030", "Блокнот для записей мини", "Тетради и блокноты", 75, 60, "supplier_004", "2026-09-05", "2026-10-05", 65, "шт", 0.08, 0.0005, "Склад В", "", "active", ""],
        
        # Папки и архивация (10 товаров)
        ["item_031", "Папка-скоросшиватель А4", "Папки и архивация", 180, 150, "supplier_001", "2026-09-01", "2026-10-01", 55, "шт", 0.08, 0.001, "Склад Г", "", "active", ""],
        ["item_032", "Папка на резинках А4", "Папки и архивация", 95, 100, "supplier_001", "2026-08-25", "2026-09-25", 75, "шт", 0.1, 0.0012, "Склад Г", "", "active", ""],
        ["item_033", "Папка с файлами А4", "Папки и архивация", 60, 80, "supplier_001", "2026-08-20", "2026-09-20", 95, "шт", 0.12, 0.0015, "Склад Г", "", "active", ""],
        ["item_034", "Папка-регистратор А4 (75мм)", "Папки и архивация", 40, 50, "supplier_001", "2026-08-22", "2026-09-22", 180, "шт", 0.45, 0.005, "Склад Г", "", "active", ""],
        ["item_035", "Файл-вкладыш А4 (100 шт)", "Папки и архивация", 25, 30, "supplier_004", "2026-08-28", "2026-09-28", 120, "упаковка", 0.8, 0.008, "Склад Г", "", "active", ""],
        ["item_036", "Разделители для папки (10 шт)", "Папки и архивация", 30, 25, "supplier_004", "2026-08-30", "2026-09-30", 85, "набор", 0.05, 0.0005, "Склад Г", "", "active", ""],
        ["item_037", "Папка-планшет А4", "Папки и архивация", 15, 20, "supplier_001", "2026-08-15", "2026-09-15", 220, "шт", 0.35, 0.004, "Склад Г", "", "active", ""],
        ["item_038", "Папка на молнии А4", "Папки и архивация", 28, 30, "supplier_001", "2026-08-28", "2026-09-28", 145, "шт", 0.15, 0.002, "Склад Г", "", "active", ""],
        ["item_039", "Короб архивный А4", "Папки и архивация", 10, 15, "supplier_001", "2026-05-10", "2026-06-10", 280, "шт", 0.6, 0.01, "Склад Г", "", "active", ""],
        ["item_040", "Папка для презентаций А4", "Папки и архивация", 22, 25, "supplier_004", "2026-08-20", "2026-09-20", 195, "шт", 0.2, 0.0025, "Склад Г", "", "active", ""],
        
        # Клей и скотч (10 товаров)
        ["item_041", "Клей-карандаш 21г", "Клей и скотч", 45, 50, "supplier_002", "2026-08-22", "2026-09-22", 55, "шт", 0.025, 0.0002, "Склад Д", "", "active", ""],
        ["item_042", "Клей ПВА 100мл", "Клей и скотч", 30, 35, "supplier_004", "2026-08-25", "2026-09-25", 75, "флакон", 0.12, 0.001, "Склад Д", "", "active", ""],
        ["item_043", "Клей канцелярский силикатный", "Клей и скотч", 18, 20, "supplier_002", "2026-08-15", "2026-09-15", 65, "флакон", 0.15, 0.0012, "Склад Д", "", "active", ""],
        ["item_044", "Скотч канцелярский прозрачный", "Клей и скотч", 55, 50, "supplier_004", "2026-09-01", "2026-10-01", 45, "рулон", 0.08, 0.0008, "Склад Д", "", "active", ""],
        ["item_045", "Скотч двухсторонний", "Клей и скотч", 20, 25, "supplier_004", "2026-08-18", "2026-09-18", 85, "рулон", 0.1, 0.001, "Склад Д", "", "active", ""],
        ["item_046", "Ножницы офисные 21см", "Клей и скотч", 25, 20, "supplier_002", "2026-08-28", "2026-09-28", 120, "шт", 0.08, 0.0008, "Склад Д", "", "active", ""],
        ["item_047", "Ножницы маленькие 13см", "Клей и скотч", 15, 15, "supplier_002", "2026-08-20", "2026-09-20", 85, "шт", 0.05, 0.0005, "Склад Д", "", "active", ""],
        ["item_048", "Нож канцелярский большой", "Клей и скотч", 12, 15, "supplier_004", "2026-08-15", "2026-09-15", 95, "шт", 0.06, 0.0006, "Склад Д", "", "active", ""],
        ["item_049", "Лезвия для ножа (10 шт)", "Клей и скотч", 8, 10, "supplier_004", "2026-05-15", "2026-06-15", 65, "упаковка", 0.03, 0.0003, "Склад Д", "", "active", ""],
        ["item_050", "Диспенсер для скотча", "Клей и скотч", 10, 12, "supplier_004", "2026-05-05", "2026-06-05", 180, "шт", 0.25, 0.003, "Склад Д", "", "active", ""],
        
        # Степлеры и дыроколы (10 товаров)
        ["item_051", "Степлер офисный №24/6", "Степлеры и дыроколы", 18, 15, "supplier_004", "2026-08-28", "2026-09-28", 250, "шт", 0.35, 0.004, "Склад Е", "", "active", ""],
        ["item_052", "Степлер мини", "Степлеры и дыроколы", 25, 20, "supplier_004", "2026-08-25", "2026-09-25", 145, "шт", 0.2, 0.002, "Склад Е", "", "active", ""],
        ["item_053", "Скобы для степлера №24/6 (1000 шт)", "Степлеры и дыроколы", 40, 35, "supplier_001", "2026-09-01", "2026-10-01", 85, "упаковка", 0.15, 0.0015, "Склад Е", "", "active", ""],
        ["item_054", "Антистеплер", "Степлеры и дыроколы", 12, 10, "supplier_004", "2026-08-30", "2026-09-30", 95, "шт", 0.12, 0.001, "Склад Е", "", "active", ""],
        ["item_055", "Дырокол офисный", "Степлеры и дыроколы", 8, 10, "supplier_004", "2026-08-15", "2026-09-15", 320, "шт", 0.8, 0.01, "Склад Е", "", "active", ""],
        ["item_056", "Дырокол мощный (30 листов)", "Степлеры и дыроколы", 3, 5, "supplier_004", "2026-04-10", "2026-05-10", 580, "шт", 1.2, 0.015, "Склад Е", "", "active", ""],
        ["item_057", "Удалитель скоб", "Степлеры и дыроколы", 15, 12, "supplier_004", "2026-08-20", "2026-09-20", 75, "шт", 0.08, 0.0008, "Склад Е", "", "active", ""],
        ["item_058", "Степлер электрический", "Степлеры и дыроколы", 2, 3, "supplier_005", "2026-03-20", "2026-04-20", 2500, "шт", 2.5, 0.03, "Склад Е", "", "active", ""],
        ["item_059", "Скобы для степлера №10 (1000 шт)", "Степлеры и дыроколы", 30, 25, "supplier_001", "2026-08-28", "2026-09-28", 65, "упаковка", 0.1, 0.001, "Склад Е", "", "active", ""],
        ["item_060", "Дырокол однодырочный", "Степлеры и дыроколы", 6, 8, "supplier_004", "2026-05-15", "2026-06-15", 180, "шт", 0.25, 0.003, "Склад Е", "", "active", ""],
    ]
    
    for item in items_data:
        ws.append(item)
    
    # Автоширина колонок
    for col_idx, header in enumerate(headers, 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = max(len(str(header)) + 2, 15)
    
    # Создаём директорию data если её нет
    data_dir = Path(__file__).parent.parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Сохраняем файл
    file_path = data_dir / "items.xlsx"
    wb.save(file_path)
    print(f"✓ Создан файл {file_path} с {len(items_data)} товарами")


def create_suppliers_excel():
    """Создаёт Excel-файл с поставщиками."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Поставщики"
    
    # Заголовки
    headers = [
        "supplier_id", "company_name", "contact_person", "phone", "email",
        "contract_start", "contract_end", "payment_terms", "rating",
        "last_contact", "status"
    ]
    ws.append(headers)
    
    # Данные поставщиков (5 поставщиков)
    suppliers_data = [
        ["supplier_001", "КанцТорг ООО", "Иванов Иван Иванович", "+7 (495) 123-45-67", "ivanov@kanctorg.ru", "2026-01-01", "2026-12-31", "предоплата 100%", 4.8, "2026-09-05", "active"],
        ["supplier_002", "ОфисМастер ЗАО", "Петрова Мария Сергеевна", "+7 (495) 234-56-78", "petrova@ofismaster.ru", "2026-01-01", "2026-12-31", "50% предоплата", 3.5, "2026-07-15", "problem"],
        ["supplier_003", "БумагаСервис ООО", "Сидоров Алексей Петрович", "+7 (495) 345-67-89", "sidorov@bumagaservice.ru", "2026-01-01", "2026-12-31", "постоплата 14 дней", 4.9, "2026-09-10", "active"],
        ["supplier_004", "КанцелярияПлюс ИП", "Козлова Елена Владимировна", "+7 (495) 456-78-90", "kozlova@kancplus.ru", "2026-01-01", "2026-12-31", "предоплата 100%", 4.2, "2026-08-28", "active"],
        ["supplier_005", "ОфисТехника ООО", "Морозов Дмитрий Константинович", "+7 (495) 567-89-01", "morozov@ofistech.ru", "2026-01-01", "2026-12-31", "постоплата 30 дней", 4.6, "2026-06-01", "problem"],
    ]
    
    for supplier in suppliers_data:
        ws.append(supplier)
    
    # Автоширина колонок
    for col_idx, header in enumerate(headers, 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = max(len(str(header)) + 2, 15)
    
    # Создаём директорию data если её нет
    data_dir = Path(__file__).parent.parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Сохраняем файл
    file_path = data_dir / "suppliers.xlsx"
    wb.save(file_path)
    print(f"✓ Создан файл {file_path} с {len(suppliers_data)} поставщиками")


def create_supplier_files():
    """Создаёт текстовые файлы для каждого поставщика."""
    data_dir = Path(__file__).parent.parent.parent / "data" / "suppliers"
    
    suppliers_info = [
        {
            "id": "supplier_001",
            "name": "КанцТорг ООО",
            "contact": "Иванов Иван Иванович",
            "phone": "+7 (495) 123-45-67",
            "email": "ivanov@kanctorg.ru",
            "address": "г. Москва, ул. Ленина, д. 10",
            "contract_num": "КТ-2026-001",
            "min_order": "5 000",
            "payment": "предоплата 100%",
            "delivery": "3-5 рабочих дней",
            "rating": "4.8",
            "total_orders": "45",
            "total_amount": "487 500",
            "avg_check": "10 833",
            "delays": "2 (4.4%)",
            "returns": "0",
        },
        {
            "id": "supplier_002",
            "name": "ОфисМастер ЗАО",
            "contact": "Петрова Мария Сергеевна",
            "phone": "+7 (495) 234-56-78",
            "email": "petrova@ofismaster.ru",
            "address": "г. Москва, ул. Пушкина, д. 25",
            "contract_num": "ОМ-2026-002",
            "min_order": "3 000",
            "payment": "50% предоплата",
            "delivery": "5-7 рабочих дней",
            "rating": "3.5",
            "total_orders": "38",
            "total_amount": "245 600",
            "avg_check": "6 463",
            "delays": "12 (31.6%)",
            "returns": "3",
        },
        {
            "id": "supplier_003",
            "name": "БумагаСервис ООО",
            "contact": "Сидоров Алексей Петрович",
            "phone": "+7 (495) 345-67-89",
            "email": "sidorov@bumagaservice.ru",
            "address": "г. Москва, ул. Гагарина, д. 15",
            "contract_num": "БС-2026-003",
            "min_order": "10 000",
            "payment": "постоплата 14 дней",
            "delivery": "2-3 рабочих дня",
            "rating": "4.9",
            "total_orders": "52",
            "total_amount": "624 000",
            "avg_check": "12 000",
            "delays": "0 (0%)",
            "returns": "0",
        },
        {
            "id": "supplier_004",
            "name": "КанцелярияПлюс ИП",
            "contact": "Козлова Елена Владимировна",
            "phone": "+7 (495) 456-78-90",
            "email": "kozlova@kancplus.ru",
            "address": "г. Москва, ул. Чехова, д. 8",
            "contract_num": "КП-2026-004",
            "min_order": "2 000",
            "payment": "предоплата 100%",
            "delivery": "4-6 рабочих дней",
            "rating": "4.2",
            "total_orders": "41",
            "total_amount": "328 000",
            "avg_check": "8 000",
            "delays": "5 (12.2%)",
            "returns": "1",
        },
        {
            "id": "supplier_005",
            "name": "ОфисТехника ООО",
            "contact": "Морозов Дмитрий Константинович",
            "phone": "+7 (495) 567-89-01",
            "email": "morozov@ofistech.ru",
            "address": "г. Москва, ул. Техническая, д. 42",
            "contract_num": "ОТ-2026-005",
            "min_order": "15 000",
            "payment": "постоплата 30 дней",
            "delivery": "5-10 рабочих дней",
            "rating": "4.6",
            "total_orders": "28",
            "total_amount": "420 000",
            "avg_check": "15 000",
            "delays": "1 (3.6%)",
            "returns": "0",
        },
    ]
    
    for supplier in suppliers_info:
        supplier_dir = data_dir / supplier["id"]
        supplier_dir.mkdir(parents=True, exist_ok=True)
        
        # contract.txt
        contract_content = f"""# Поставщик {supplier["id"]} - {supplier["name"]}

## Информация о поставщике
- Название: {supplier["name"]}
- Контактное лицо: {supplier["contact"]}
- Телефон: {supplier["phone"]}
- Email: {supplier["email"]}
- Адрес: {supplier["address"]}

## Условия договора
- Номер договора: {supplier["contract_num"]}
- Дата начала: 01.01.2026
- Дата окончания: 31.12.2026
- Условия оплаты: {supplier["payment"]}
- Срок поставки: {supplier["delivery"]}
- Минимальная сумма заказа: {supplier["min_order"]} руб.

## Примечания
- Рейтинг поставщика: {supplier["rating"]}/5.0
- Работает с 2020 года
"""
        (supplier_dir / "contract.txt").write_text(contract_content, encoding="utf-8")
        
        # quality_notes.txt
        quality_content = f"""# Заметки о качестве - Поставщик {supplier["id"]}

## Общая оценка качества
- Рейтинг: {supplier["rating"]}/5.0
- Брак: менее 1%

## Примечания
- Стабильное качество на протяжении 2 лет
- При обнаружении брака поставщик быстро заменяет товар
- Товары соответствуют заявленным характеристикам
"""
        (supplier_dir / "quality_notes.txt").write_text(quality_content, encoding="utf-8")
        
        # order_history.txt
        history_content = f"""# История заказов - Поставщик {supplier["id"]}

## Статистика за 2026 год
- Всего заказов: {supplier["total_orders"]}
- Общая сумма: {supplier["total_amount"]} руб.
- Средний чек: {supplier["avg_check"]} руб.
- Задержек поставки: {supplier["delays"]}
- Возвратов товара: {supplier["returns"]}

## Последние заказы
- Заказ от 15.11.2026 - Доставлен в срок
- Заказ от 10.11.2026 - Доставлен с задержкой 1 день
- Заказ от 05.11.2026 - Доставлен в срок
"""
        (supplier_dir / "order_history.txt").write_text(history_content, encoding="utf-8")
        
        print(f"✓ Созданы файлы для {supplier['name']}")


if __name__ == "__main__":
    print("🚀 Начинаю генерацию тестовых данных...\n")
    
    create_items_excel()
    create_suppliers_excel()
    create_supplier_files()
    
    print("\n✅ Генерация данных завершена!")
```

### 2.2. Запуск скрипта

Запусти скрипт для генерации тестовых данных:

```bash
cd backend
python scripts/generate_test_data.py
```

Это создаст:
- `data/items.xlsx` — 60 товаров канцелярии
- `data/suppliers.xlsx` — 5 поставщиков
- `data/suppliers/supplier_001/` — файлы поставщика (contract.txt, quality_notes.txt, order_history.txt)
- `data/suppliers/supplier_002/` — файлы поставщика
- `data/suppliers/supplier_003/` — файлы поставщика
- `data/suppliers/supplier_004/` — файлы поставщика
- `data/suppliers/supplier_005/` — файлы поставщика

---

## ЭТАП 3: ЗАПУСК И ТЕСТИРОВАНИЕ

### 3.1. Установка зависимостей

#### Backend:

```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

#### Frontend:

```bash
cd ..
npm install
```

### 3.2. Настройка .env

Создай файл `backend/.env`:

```env
# OpenAI API
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4o-mini

# MCP HTTP сервер
MCP_SERVER_URL=http://localhost:8001/mcp
MCP_SERVER_PORT=8001
```

Замени `sk-your-actual-key-here` на твой реальный OpenAI API ключ.

### 3.3. Запуск MCP-сервера

В первом терминале:

```bash
cd backend
python mcp_server/server.py
```

Должно появиться:
```
[Warehouse MCP Server] Запуск HTTP сервера на 0.0.0.0:8001...
[Warehouse MCP Server] URL: http://0.0.0.0:8001
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### 3.4. Запуск Backend

Во втором терминале:

```bash
cd backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Должно появиться:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
[Startup] ItemsService initialized
[Startup] SuppliersService initialized
[Startup] MCP Client initialized
[Startup] Available MCP tools: 4
```

### 3.5. Запуск Frontend

В третьем терминале:

```bash
npm run dev
```

Должно появиться:
```
VITE ready in xxx ms
➜  Local:   http://localhost:3000/
```

### 3.6. Тестирование

Открой браузер на http://localhost:3000

Попробуй следующие запросы:

1. **Общий вопрос:**
   ```
   Что ты умеешь?
   ```

2. **Анализ товаров с дефицитом:**
   ```
   Проанализируй товары с дефицитом
   ```

3. **Проверка условий заказа:**
   ```
   Проверь условия заказа у поставщика supplier_001
   ```

4. **Подтверждение заказа:**
   ```
   Закажи товары у поставщика supplier_001
   ```
   (после этого появится диалог подтверждения)

---

## ЭТАП 4: ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ

### 4.1. Проверка MCP-сервера

Проверь, что MCP-сервер работает:

```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "list_tools_info",
      "arguments": {}
    }
  }'
```

Должен вернуться список инструментов.

### 4.2. Проверка Backend API

Проверь health check:

```bash
curl http://localhost:8000/health
```

Должно вернуться:
```json
{"status": "ok"}
```

### 4.3. Проверка SSE

Открой браузер на http://localhost:3000, введи запрос и нажми "Запустить".

В журнале выполнения должны появиться события:
- `run_started`
- `node_started` (parse_request)
- `route_detected`
- `node_finished` (parse_request)
- `node_started` (load_items)
- `tool_started` (mcp.get_items)
- `tool_finished` (mcp.get_items)
- и т.д.

---

## ЭТАП 5: РЕШЕНИЕ ПРОБЛЕМ

### 5.1. Если MCP-сервер не запускается

Проверь, что установлен `mcp[cli]>=2.0.0`:

```bash
pip list | grep mcp
```

Если не установлен:

```bash
pip install "mcp[cli]>=2.0.0"
```

### 5.2. Если backend не видит MCP-сервер

Проверь, что MCP-сервер запущен на порту 8001:

```bash
curl http://localhost:8001/health
```

Если не отвечает, перезапусти MCP-сервер.

### 5.3. Если frontend не отображается

Проверь, что frontend запущен на порту 3000:

```bash
curl http://localhost:3000
```

Если не отвечает, перезапусти frontend:

```bash
npm run dev
```

### 5.4. Если OpenAI API не работает

Проверь, что OPENAI_API_KEY указан в `backend/.env`:

```bash
cat backend/.env | grep OPENAI_API_KEY
```

Если не указан, добавь его.

Проверь, что на счету OpenAI есть кредиты:
https://platform.openai.com/account/billing

---

## ЭТАП 6: ФИНАЛЬНАЯ ПРОВЕРКА

### 6.1. Проверка всех сценариев

Протестируй все 4 сценария:

1. ✅ Общий вопрос
2. ✅ Анализ товаров с дефицитом
3. ✅ Проверка условий заказа
4. ✅ Подтверждение заказа

### 6.2. Проверка логов

Проверь, что в логах backend появляются все события:
- `[parse_request]`
- `[route_request]`
- `[load_items]`
- `[find_problem_items]`
- `[analyze_items]`
- `[load_supplier_files]`
- `[check_order_conditions]`
- `[confirm_order]`

### 6.3. Проверка SSE событий

Проверь, что в журнале выполнения на frontend появляются все события:
- `run_started`
- `node_started` / `node_finished`
- `tool_started` / `tool_finished`
- `route_detected`
- `action_pending` (для сценария 4)
- `action_resolved` (для сценария 4)
- `run_finished`

---

## ЭТАП 7: ДОКУМЕНТАЦИЯ

### 7.1. Обновление README.md

Убедись, что README.md содержит:
- Описание проекта
- Архитектуру
- Инструкции по установке
- Инструкции по запуску
- Примеры использования
- Решение проблем

### 7.2. Создание CHANGELOG.md

Создай файл `CHANGELOG.md`:

```markdown
# Changelog

## [0.8.0] - 2026-09-12

### Добавлено
- AI-оператор склада канцелярии
- LangGraph workflow с MCP интеграцией
- Анализ товаров с дефицитом
- Проверка условий заказа у поставщиков
- Подтверждение заказов с HITL
- SSE для real-time обновлений
- MCP-сервер для работы с Excel-таблицами
- 60 тестовых товаров канцелярии
- 5 тестовых поставщиков с файлами

### Изменено
- N/A

### Удалено
- N/A
```

---

## ЭТАП 8: ФИНАЛЬНАЯ СБОРКА

### 8.1. Сборка frontend

```bash
npm run build
```

Должно появиться:
```
✓ built in x.xx s
```

### 8.2. Проверка dist/

Проверь, что создана папка `dist/` с собранными файлами:

```bash
ls dist/
```

Должны быть файлы:
- `index.html`
- `assets/index-xxx.js`
- `assets/index-xxx.css`

---

## ЭТАП 9: ФИНАЛЬНАЯ ПРОВЕРКА

### 9.1. Проверка всех файлов

Убедись, что все файлы созданы:

**Backend:**
- ✅ `backend/main.py`
- ✅ `backend/config.py`
- ✅ `backend/.env`
- ✅ `backend/requirements.txt`
- ✅ `backend/api/routes.py`
- ✅ `backend/api/run_manager.py`
- ✅ `backend/graph/state.py`
- ✅ `backend/graph/workflow.py`
- ✅ `backend/graph/nodes/*.py` (все узлы)
- ✅ `backend/mcp_server/server.py`
- ✅ `backend/mcp_server/items_service.py`
- ✅ `backend/mcp_server/suppliers_service.py`
- ✅ `backend/mcp_server/schemas.py`
- ✅ `backend/mcp_server/validation.py`
- ✅ `backend/mcp_client/client.py`

**Frontend:**
- ✅ `src/App.tsx`
- ✅ `src/main.tsx`
- ✅ `src/index.css`
- ✅ `src/types.ts`
- ✅ `src/components/Header.tsx`
- ✅ `src/components/RunInput.tsx`
- ✅ `src/components/AnswerPanel.tsx`
- ✅ `src/components/ExecutionLog.tsx`
- ✅ `src/components/ActionApproval.tsx`

**Данные:**
- ✅ `data/items.xlsx`
- ✅ `data/suppliers.xlsx`
- ✅ `data/suppliers/supplier_001/` (contract.txt, quality_notes.txt, order_history.txt)
- ✅ `data/suppliers/supplier_002/` (contract.txt, quality_notes.txt, order_history.txt)
- ✅ `data/suppliers/supplier_003/` (contract.txt, quality_notes.txt, order_history.txt)
- ✅ `data/suppliers/supplier_004/` (contract.txt, quality_notes.txt, order_history.txt)
- ✅ `data/suppliers/supplier_005/` (contract.txt, quality_notes.txt, order_history.txt)

### 9.2. Финальный тест

Запусти все три сервера и протестируй все 4 сценария.

Убедись, что:
- ✅ Все сценарии работают
- ✅ Все логи появляются
- ✅ Все SSE события отображаются
- ✅ Подтверждение заказа работает
- ✅ Сборка проходит успешно

---

## ГОТОВО! 🎉

Поздравляю! Ты создал полноценный AI-оператор склада канцелярии с нуля!

Теперь у тебя есть:
- ✅ Backend на Python (FastAPI + LangGraph + OpenAI + MCP)
- ✅ Frontend на React (Vite + TypeScript + Tailwind CSS)
- ✅ MCP-сервер для работы с Excel-таблицами
- ✅ 60 тестовых товаров канцелярии
- ✅ 5 тестовых поставщиков с файлами
- ✅ 4 рабочих сценария
- ✅ HITL для подтверждения заказов
- ✅ SSE для real-time обновлений

Ты можешь расширять проект, добавляя новые сценарии, новые MCP-инструменты, новые данные.

Удачи! 🚀
