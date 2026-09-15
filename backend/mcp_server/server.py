"""
MCP Server для работы с Excel-таблицей товаров склада канцелярии.
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
    
    print(f"[Excel MCP Server] Запуск HTTP сервера на {host}:{port}...", file=sys.stderr)
    print(f"[Excel MCP Server] URL: http://{host}:{port}", file=sys.stderr)
    
    # Запускаем через mcp.run() с streamable-http транспортом
    mcp.run(
        transport="streamable-http",
        host=host,
        port=port
    )
