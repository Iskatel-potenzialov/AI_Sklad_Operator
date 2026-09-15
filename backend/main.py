"""
Главный файл FastAPI приложения.
"""
import sys
import asyncio

# Windows: subprocess в asyncio требует ProactorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.api.admin import router as admin_router
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
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(router)
app.include_router(admin_router)


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения."""
    # Инициализируем SQLite
    from backend.db import init_db
    await init_db()

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
        # tools_info теперь может быть dict с ключом "tools" или {"result": ...}
        if isinstance(tools_info, dict):
            tools = tools_info.get("tools", [])
            if not tools and "result" in tools_info:
                # Если результат в виде строки, попробуем распарсить
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
