"""
MCP Client — обёртка для вызова MCP-инструментов склада через HTTP.

Использует streamable-http транспорт для связи с MCP-сервером.
MCP-сервер должен быть запущен отдельно:
    python backend/mcp_server/server.py

Архитектура:
  FastAPI (порт 8000)
    └── MCP Client
          └── HTTP запросы → MCP Server (порт 8001)
                └── Items Service
                      └── items.xlsx
"""
import os
import asyncio
from typing import Optional, Dict, Any

from mcp import Client


class MCPClientError(Exception):
    """Ошибка MCP-клиента."""
    def __init__(self, message: str, error_code: str = "MCP_CLIENT_ERROR"):
        super().__init__(message)
        self.error_code = error_code


class MCPClient:
    """
    HTTP-клиент для вызова MCP-инструментов склада.
    Все вызовы к товарам проходят через HTTP к MCP-серверу.
    """
    
    def __init__(self):
        self.server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001/mcp")
    
    async def _call_tool_async(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Вызвать инструмент асинхронно через HTTP.
        """
        print(f"[MCPClient] call_tool: {tool_name} (HTTP → {self.server_url})")
        
        try:
            async with Client(self.server_url) as client:
                result = await client.call_tool(tool_name, arguments)
                
                # MCP SDK v2 возвращает CallToolResult объект
                # Нужно извлечь structured_content или content
                if hasattr(result, 'structured_content') and result.structured_content:
                    data = result.structured_content
                    print(f"[MCPClient] {tool_name} result (structured): {str(data)[:100]}...")
                    return data
                elif hasattr(result, 'content') and result.content:
                    # Извлекаем текст из content
                    content_text = result.content[0].text if result.content else ""
                    print(f"[MCPClient] {tool_name} result (content): {content_text[:100]}...")
                    # Парсим JSON если это JSON
                    import json
                    try:
                        return json.loads(content_text)
                    except:
                        return {"result": content_text}
                else:
                    print(f"[MCPClient] {tool_name} result: {str(result)[:100]}...")
                    return {"result": str(result)}
                
        except Exception as e:
            print(f"[MCPClient] {tool_name} error: {e}")
            raise MCPClientError(f"Ошибка вызова инструмента: {str(e)}", "TOOL_CALL_ERROR")
    
    def _run_async(self, coro):
        """Запустить асинхронную функцию синхронно."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Если уже в async контексте, создаём новую задачу
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, coro)
                    return future.result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # Нет event loop, создаём новый
            return asyncio.run(coro)
    
    def get_items(
        self,
        item_id: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Получить список товаров через MCP (HTTP).
        
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
            result = self._run_async(self._call_tool_async("get_items", arguments))
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
        Получить данные конкретного товара через MCP (HTTP).
        
        Args:
            item_id: ID товара
            
        Returns:
            Результат в формате MCP
        """
        print(f"[MCPClient] get_item(item_id={item_id})")
        
        try:
            result = self._run_async(self._call_tool_async("get_item", {"item_id": item_id}))
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
    
    def get_suppliers(self) -> Dict[str, Any]:
        """
        Получить список поставщиков через MCP (HTTP).
        
        Returns:
            Результат в формате MCP
        """
        print(f"[MCPClient] get_suppliers()")
        
        try:
            result = self._run_async(self._call_tool_async("get_suppliers", {}))
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
    
    def update_min_stock(
        self,
        item_id: str,
        new_min_stock: int,
    ) -> Dict[str, Any]:
        """
        Изменить минимальный остаток товара через MCP (HTTP).
        
        Args:
            item_id: ID товара
            new_min_stock: новый минимальный остаток
            
        Returns:
            Результат в формате MCP
        """
        print(f"[MCPClient] update_min_stock(item_id={item_id}, new_min_stock={new_min_stock})")
        
        try:
            result = self._run_async(
                self._call_tool_async(
                    "update_min_stock",
                    {"item_id": item_id, "new_min_stock": new_min_stock}
                )
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
    
    def list_tools(self) -> Dict[str, Any]:
        """Получить список доступных инструментов."""
        try:
            return self._run_async(self._call_tool_async("list_tools_info", {}))
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
