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
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", None)  # Для локальных моделей (Qwen, Ollama) или прокси

# MCP HTTP сервер
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8001"))

# RAG (векторный поиск)
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8002")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "stationery_rag")

print(f"[OK] RAG_SERVICE_URL = {RAG_SERVICE_URL}")
print(f"[OK] QDRANT_URL = {QDRANT_URL}")
print(f"[OK] QDRANT_COLLECTION = {QDRANT_COLLECTION}")


# Отладка — проверяем что ключ загружен
if not OPENAI_API_KEY:
    print(f"[WARNING] OPENAI_API_KEY не найден в {ENV_PATH}")
else:
    print(f"[OK] OPENAI_API_KEY загружен")
    print(f"[OK] OPENAI_MODEL = {OPENAI_MODEL}")

print(f"[OK] MCP_SERVER_URL = {MCP_SERVER_URL}")
print(f"[OK] MCP_SERVER_PORT = {MCP_SERVER_PORT}")



