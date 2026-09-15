"""
Работа с SQLite: инициализация БД и сохранение заказов.
"""
import json
from pathlib import Path
import aiosqlite


DB_PATH = Path(__file__).parent.parent / "data" / "app.db"


CREATE_ORDERS_TABLE = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    supplier_id TEXT NOT NULL,
    supplier_name TEXT,
    items_json TEXT NOT NULL,
    total_cost REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'confirmed',
    telegram_sent INTEGER NOT NULL DEFAULT 0
)
"""

CREATE_EVAL_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS eval_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    avg_score REAL,
    passed INTEGER,
    total_cases INTEGER,
    precision_5 REAL,
    recall_5 REAL,
    hit_5 REAL,
    mrr REAL,
    faithfulness_avg REAL,
    faithfulness_unsupported INTEGER,
    backend_cost_rub REAL,
    judge_cost_rub REAL,
    faithfulness_cost_rub REAL,
    total_cost_rub REAL,
    duration_sec REAL,
    results_json TEXT NOT NULL
)
"""


async def init_db() -> None:
    """Создаёт таблицы, если их нет."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_ORDERS_TABLE)
        await db.execute(CREATE_EVAL_RUNS_TABLE)   # ← добавить
        await db.commit()
    print(f"[db] Initialized at {DB_PATH}")


async def save_order(order: dict) -> bool:
    """
    Сохраняет заказ.
    Возвращает True если вставлено, False если заказ с таким run_id уже существует.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                """
                INSERT INTO orders
                    (run_id, timestamp, supplier_id, supplier_name,
                     items_json, total_cost, status, telegram_sent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order["run_id"],
                    order["timestamp"],
                    order["supplier_id"],
                    order.get("supplier_name"),
                    json.dumps(order["items"], ensure_ascii=False),
                    order["total_cost"],
                    order.get("status", "confirmed"),
                    1 if order.get("telegram_sent") else 0,
                ),
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            print(f"[db] Order for run {order['run_id']} already exists")
            return False


async def mark_telegram_sent(run_id: str) -> None:
    """Помечает, что уведомление в Telegram ушло."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE orders SET telegram_sent = 1 WHERE run_id = ?",
            (run_id,),
        )
        await db.commit()


async def get_orders(limit: int = 100) -> list[dict]:
    """Возвращает последние заказы (для будущего API/UI)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders ORDER BY id DESC LIMIT ?",
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]