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
    intent: Optional[str] = None  # general_question, inventory_analysis, check_order_conditions, confirm_order
    target_item_id: Optional[str] = None
    target_supplier_id: Optional[str] = None
        # Для update_min_stock
    new_min_stock: Optional[int] = None
    scope: Optional[str] = None
    
    # Данные товаров
    items: List[Dict] = []
    suppliers: List[Dict] = []
    problem_items: List[Dict] = []
    current_item_id: Optional[str] = None
    item_context: Dict[str, Any] = {}
    
    # Данные поставщиков
    supplier_files: Dict[str, str] = {}
    items_to_order: List[Dict] = []
    total_cost: float = 0
    items_to_order: List[Dict] = []
    
    # Анализ и результаты
    analysis: Optional[Dict] = None
    recommended_actions: List[Dict] = []
    pending_action: Optional[Dict] = None
    action_approved: bool = False
    order_confirmation: Optional[Dict] = None
    
    # Ответ
    answer: Optional[str] = None
    
    # MCP данные
    mcp_results: Dict[str, dict] = {}
    
    # Внутренний трейс агентных tool calls (для UI)
    tool_trace: List[str] = []
    

    # ID чанков, найденных RAG-агентом (для retrieval-метрик)
    retrieved_chunk_ids: List[int] = []
    
    retrieved_chunks: List[Any] = []
    
    # Ошибки и статус
    errors: list[str] = []
    status: str = "pending"  # pending, running, finished, error
    
    # Маршрут (для UI)
    route_trace: List[str] = []

    class Config:
        arbitrary_types_allowed = True
