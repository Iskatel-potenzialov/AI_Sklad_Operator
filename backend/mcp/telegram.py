"""
Telegram MCP — отправка уведомлений через Telegram Bot API.
Локальный модуль (не HTTP сервер).

Использует:
   - TELEGRAM_BOT_TOKEN — токен бота
   - TELEGRAM_ADMIN_CHAT_ID — ID администратора
"""
import os
import httpx
from typing import Optional


# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")


class TelegramError(Exception):
    """Ошибка Telegram."""
    pass


async def send_telegram_message(
    chat_id: Optional[str] = None,
    message: str = "",
    parse_mode: str = "HTML"
) -> bool:
    """
    Отправить сообщение в Telegram через Bot API.
    
    Args:
        chat_id: ID чата (по умолчанию — TELEGRAM_ADMIN_CHAT_ID)
        message: Текст сообщения
        parse_mode: Режим форматирования (HTML, Markdown, MarkdownV2)
    
    Returns:
        True если сообщение успешно отправлено
    
    Raises:
        TelegramError: если произошла ошибка
    """
    # Используем admin chat_id по умолчанию
    if not chat_id:
        chat_id = TELEGRAM_ADMIN_CHAT_ID
    
    # Проверяем конфигурацию
    if not TELEGRAM_BOT_TOKEN:
        raise TelegramError("TELEGRAM_BOT_TOKEN не установлен в .env")
    
    if not chat_id:
        raise TelegramError("chat_id не указан и TELEGRAM_ADMIN_CHAT_ID не установлен")
    
    # Формируем URL API
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Формируем payload
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode,
    }
    
    # Отправляем запрос
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(api_url, json=payload)
            
            if response.status_code == 200:
                print(f"[Telegram] ✓ Сообщение отправлено в чат {chat_id}")
                return True
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                print(f"[Telegram] ✗ Ошибка отправки: {error_msg}")
                raise TelegramError(error_msg)
    
    except httpx.TimeoutException:
        raise TelegramError("Таймаут при отправке сообщения")
    except httpx.HTTPError as e:
        raise TelegramError(f"HTTP ошибка: {str(e)}")


def format_order_message(
    supplier_name: str,
    items: list,
    total_cost: float
) -> str:
    """
    Форматировать сообщение о заказе для Telegram.
    
    Args:
        supplier_name: Название поставщика
        items: Список товаров для заказа
        total_cost: Общая стоимость заказа
    
    Returns:
        Отформатированное сообщение в HTML формате
    """
    lines = [
        "<b>📦 Новый заказ</b>",
        "",
        f"<b>Поставщик:</b> {supplier_name}",
        "",
        "<b>Товары:</b>",
    ]
    
    for item in items:
        item_name = item.get("product_name", item.get("item_id", "N/A"))
        quantity = item.get("quantity", 0)
        unit = item.get("unit_of_measure", "шт")
        lines.append(f"  • {item_name} — {quantity} {unit}")
    
    lines.extend([
        "",
        f"<b>Общая стоимость:</b> {total_cost:.2f} руб.",
        "",
        "<i>Отправлено AI-оператором склада</i>",
    ])
    
    return "\n".join(lines)
