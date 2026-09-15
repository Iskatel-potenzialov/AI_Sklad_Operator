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
