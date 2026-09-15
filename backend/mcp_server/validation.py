"""
Валидация данных для MCP-инструментов склада канцелярии.
"""
from typing import List, Set

# Допустимые значения статусов товаров
VALID_ITEM_STATUSES = {"active", "inactive", "discontinued"}

# Обязательные колонки в Excel для товаров
REQUIRED_ITEM_COLUMNS = {
    "item_id",
    "product_name",
    "category",
    "quantity",
    "min_stock",
    "supplier_id",
    "last_ordered",
    "reorder_date",
    "unit_price",
    "unit_of_measure",
    "weight_kg",
    "volume_m3",
    "location",
    "expiry_date",
    "status",
    "ai_status",
}


def validate_item_status(status: str) -> tuple[bool, str]:
    """Проверить допустимость статуса товара."""
    if status not in VALID_ITEM_STATUSES:
        return False, f"Недопустимый статус '{status}'. Допустимые: {', '.join(sorted(VALID_ITEM_STATUSES))}"
    return True, ""


def validate_item_id(item_id: str) -> tuple[bool, str]:
    """Проверить формат item_id."""
    if not item_id or not isinstance(item_id, str):
        return False, "item_id должен быть непустой строкой"
    if len(item_id) > 100:
        return False, "item_id слишком длинный"
    return True, ""


def validate_excel_columns(columns: List[str], required: Set[str]) -> tuple[bool, str]:
    """Проверить что в Excel есть все обязательные колонки."""
    columns_set = set(columns)
    missing = required - columns_set
    if missing:
        return False, f"В Excel отсутствуют колонки: {', '.join(sorted(missing))}"
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
