"""
Схемы входных и выходных данных для MCP-инструментов склада канцелярии.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============================================================
# Входные параметры (Input Schemas)
# ============================================================

class GetItemsInput(BaseModel):
    """Входные параметры для get_items."""
    item_id: Optional[str] = Field(
        None,
        description="ID товара. Если не указан — вернуть все товары."
    )
    category: Optional[str] = Field(
        None,
        description="Фильтр по категории: Бумага, Письменные принадлежности, и т.д."
    )


class GetItemInput(BaseModel):
    """Входные параметры для get_item."""
    item_id: str = Field(
        ...,
        description="ID товара, например 'item_001'"
    )


class UpdateMinStockInput(BaseModel):
    """Входные параметры для update_min_stock."""
    item_id: str = Field(..., description="ID товара")
    new_min_stock: int = Field(
        ...,
        description="Новый минимальный остаток",
        ge=0
    )


# ============================================================
# Выходные данные (Output Schemas)
# ============================================================

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


class GetSuppliersOutput(BaseModel):
    """Результат get_suppliers."""
    success: bool
    suppliers: List[SupplierData] = []
    count: int = 0
    error: Optional[str] = None
    error_code: Optional[str] = None


# ============================================================
# Описания инструментов (Tool Descriptions)
# ============================================================

TOOL_DESCRIPTIONS = {
    "get_items": {
        "name": "get_items",
        "description": "Получить список товаров из Excel-таблицы склада. Можно получить все товары или один по ID.",
        "input_schema": GetItemsInput.model_json_schema(),
        "output_schema": GetItemsOutput.model_json_schema(),
    },
    "get_item": {
        "name": "get_item",
        "description": "Получить данные конкретного товара по ID.",
        "input_schema": GetItemInput.model_json_schema(),
        "output_schema": GetItemOutput.model_json_schema(),
    },
    "update_min_stock": {
        "name": "update_min_stock",
        "description": "Изменить минимальный остаток товара в Excel-таблице.",
        "input_schema": UpdateMinStockInput.model_json_schema(),
        "output_schema": UpdateMinStockOutput.model_json_schema(),
    },
}
