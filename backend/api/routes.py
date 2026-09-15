"""
FastAPI роуты для AI-оператора.
"""
import asyncio
import json
import traceback
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from langgraph.types import Command

from backend.api.run_manager import run_manager
from backend.graph.workflow import compiled_graph
from backend.graph.state import GraphState

router = APIRouter(prefix="/api")


class RunRequest(BaseModel):
    """Запрос на запуск workflow."""
    request: str


class RunResponse(BaseModel):
    """Ответ с ID запуска."""
    run_id: str
    status: str


class ApprovalRequest(BaseModel):
    """Запрос на подтверждение/отклонение действия."""
    approved: bool


# Описания узлов для UI
NODE_LABELS = {
    "parse_request": "Определение задачи",
    "answer_general": "Общий ответ",
    "load_items": "Загрузка товаров через MCP",
    "find_problem_items": "Поиск проблемных товаров",
    "analyze_items": "Анализ товаров",
    "load_supplier_files": "Загрузка файлов поставщика",
    "check_order_conditions": "Проверка условий заказа",
    "confirm_order": "Подтверждение заказа",
    "prepare_update": "Подготовка изменения",
    "execute_update": "Выполнение изменения",
    "search_knowledge": "Поиск в базе знаний",
}


def _events_for_node(node_name: str, state_update: dict) -> list[dict]:
    """Формирует список SSE-событий для одного узла."""
    label = NODE_LABELS.get(node_name, node_name)
    events = [
        {"type": "node_started", "node": node_name, "label": label},
    ]

    if node_name == "parse_request":
        events.append({
            "type": "route_detected",
            "intent": state_update.get("intent", "unknown"),
            "message": f"Определена задача: {state_update.get('intent', 'unknown')}",
        })

    # Пробрасываем внутренние tool calls RAG-агента на фронт
    tool_trace = state_update.get("tool_trace")
    # Пробрасываем retrieved chunk_ids для retrieval-метрик
        
        # Пробрасываем retrieved chunks для retrieval-метрик + Faithfulness
    retrieved_ids = state_update.get("retrieved_chunk_ids") or []
    retrieved_chunks = state_update.get("retrieved_chunks") or []
    print(f"[DEBUG retrieval] node={node_name} ids={len(retrieved_ids)} chunks={len(retrieved_chunks)}")
    if retrieved_ids:
        events.append({
            "type": "retrieval_done",
            "chunk_ids": retrieved_ids,
            "chunks": retrieved_chunks,
        }) 
        
    

    if tool_trace:
        for line in tool_trace:
            events.append({
                "type": "tool_started",
                "tool": line,
            })

    if state_update.get("answer"):
        events.append({
            "type": "assistant_message",
            "content": state_update["answer"],
        })

    events.append({"type": "node_finished", "node": node_name, "label": label})
    return events


def _extract_pending_action(value) -> dict | None:
    """
    Достаёт pending_action из payload interrupt().
    astream отдаёт __interrupt__ как tuple/list из Interrupt-объектов.
    Структура: (Interrupt(value={'pending_action': {...}}),)
    """
    if not isinstance(value, (tuple, list)):
        return None
    for item in value:
        payload = getattr(item, "value", None)
        if isinstance(payload, dict) and "pending_action" in payload:
            return payload["pending_action"]
    return None


async def _consume_stream(run, config: dict, stream_input) -> None:
    """
    Общий обработчик astream (старт и resume).
    Отправляет SSE-события по мере выполнения узлов и обновляет run.graph_state.

    Ключ '__interrupt__' — не узел, а payload вызова interrupt().
    Извлекаем из него pending_action и кладём в run.
    """
    async for chunk in compiled_graph.astream(
        stream_input,
        config=config,
        stream_mode="updates",
    ):
        for node_name, state_update in chunk.items():

            # interrupt() — извлекаем proposal
            if node_name == "__interrupt__":
                print(f"[_consume_stream] __interrupt__ payload: {state_update!r}")
                pending_action = _extract_pending_action(state_update)
                if pending_action:
                    run.pending_action = pending_action
                    print(f"[_consume_stream] ✓ pending_action captured from __interrupt__")
                continue

            # прочие служебные ключи langgraph
            if node_name.startswith("__"):
                continue

            if not isinstance(state_update, dict):
                continue

            for event in _events_for_node(node_name, state_update):
                await run_manager.emit_event(run.run_id, event)

            if run.graph_state:
                run.graph_state.update(state_update)
            else:
                run.graph_state = dict(state_update)


async def _handle_interrupt_or_finish(run, config: dict) -> None:
    """
    Вызывается ПОСЛЕ завершения astream.
    Определяет: граф остановлен на interrupt или завершился.
    """
    state_snapshot = await compiled_graph.aget_state(config)

    # Граф стоит на interrupt — ждём подтверждения
    if state_snapshot.next:
        print(f"[_handle_interrupt_or_finish] interrupt detected, next={state_snapshot.next}")

        # 1. Сначала — что уже поймали из __interrupt__ в _consume_stream
        pending_action = run.pending_action

        # 2. Fallback — из state.values
        if pending_action is None and state_snapshot.values:
            pending_action = state_snapshot.values.get("pending_action")

        run.status = "waiting_approval"
        run.pending_action = pending_action

        if pending_action:
            await run_manager.emit_event(run.run_id, {
                "type": "action_pending",
                "action": pending_action,
            })
            print(f"[_handle_interrupt_or_finish] ✓ action_pending sent")
        else:
            await run_manager.emit_event(run.run_id, {
                "type": "waiting_approval",
                "message": "Ожидается подтверждение действия",
            })
            print(f"[_handle_interrupt_or_finish] ⚠ pending_action не найден")
        return

    
    # Граф завершился
    final_state = run.graph_state or {}
    errors = final_state.get("errors", [])

    # Итоговая стоимость backend-вызовов
    from backend.graph.nodes.utils import get_run_cost
    backend_cost = get_run_cost(run.run_id)

    if errors:
        await run_manager.emit_event(run.run_id, {
            "type": "error",
            "message": "; ".join(errors),
            "backend_cost": backend_cost,
        })
        run.status = "error"
    else:
        await run_manager.emit_event(run.run_id, {
            "type": "run_finished",
            "answer": final_state.get("answer", ""),
            "backend_cost": backend_cost,
        })
        run.status = "finished"

@router.post("/run", response_model=RunResponse)
async def create_run(req: RunRequest):
    """
    POST /api/run
    Создаёт новый запуск workflow.
    """
    if not req.request.strip():
        raise HTTPException(status_code=400, detail="Request cannot be empty")

    run = run_manager.create_run(req.request.strip())
    run.status = "running"

    await run_manager.emit_event(run.run_id, {
        "type": "run_started",
        "run_id": run.run_id,
    })

    print(f"[create_run] Starting workflow for run {run.run_id}")
    asyncio.create_task(_execute_workflow(run.run_id, req.request.strip()))

    return RunResponse(run_id=run.run_id, status="running")


@router.post("/run/{run_id}/approve")
async def approve_action(run_id: str, req: ApprovalRequest):
    """
    POST /api/run/{run_id}/approve
    Подтверждает или отклоняет ожидающее действие (HITL).
    """
    run = run_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status != "waiting_approval":
        raise HTTPException(status_code=400, detail="Run is not waiting for approval")

    print(f"[approve_action] Run {run_id}: approved={req.approved}")

    run.approved = req.approved
    run.status = "running"

    await run_manager.emit_event(run_id, {
        "type": "action_resolved",
        "approved": req.approved,
    })

    asyncio.create_task(_resume_workflow(run_id))

    return {"status": "resumed", "approved": req.approved}


async def _execute_workflow(run_id: str, user_request: str):
    """
    Выполняет LangGraph workflow в фоновой задаче.
    Отправляет SSE-события по мере выполнения узлов.
    """
    print(f"[_execute_workflow] === STARTED for run {run_id} ===")

    # Устанавливаем run_id для аккумулятора стоимости LLM
    from backend.graph.nodes.utils import set_current_run_id
    set_current_run_id(run_id)

    run = run_manager.get_run(run_id)
    if not run:
        print(f"[_execute_workflow] Run not found: {run_id}")
        return

    try:
        initial_state = GraphState(run_id=run_id, user_request=user_request)
        run.graph_state = initial_state.model_dump()

        config = {"configurable": {"thread_id": run_id}}

        await _consume_stream(run, config, initial_state.model_dump())
        await _handle_interrupt_or_finish(run, config)

    except Exception as e:
        print(f"[_execute_workflow] ERROR: {e}")
        traceback.print_exc()
        await run_manager.emit_event(run_id, {
            "type": "error",
            "message": f"Workflow error: {str(e)}",
        })
        if run:
            run.status = "error"

    print(f"[_execute_workflow] === FINISHED for run {run_id} ===")


async def _resume_workflow(run_id: str):
    """
    Возобновляет workflow после подтверждения/отклонения действия.
    Использует Command(resume=...) и astream для сохранения потока событий.
    """
    print(f"[_resume_workflow] === RESUMING for run {run_id} ===")

    run = run_manager.get_run(run_id)
    if not run:
        print(f"[_resume_workflow] Run not found: {run_id}")
        return

    try:
        config = {"configurable": {"thread_id": run_id}}
        action_approved = bool(run.approved)

        print(f"[_resume_workflow] action_approved: {action_approved}")

        await _consume_stream(
            run,
            config,
            Command(resume={"approved": action_approved}),
        )
        await _handle_interrupt_or_finish(run, config)

    except Exception as e:
        print(f"[_resume_workflow] ERROR: {e}")
        traceback.print_exc()
        await run_manager.emit_event(run_id, {
            "type": "error",
            "message": f"Resume error: {str(e)}",
        })
        if run:
            run.status = "error"

    print(f"[_resume_workflow] === FINISHED for run {run_id} ===")


@router.get("/run/{run_id}/events")
async def stream_events(run_id: str):
    """
    GET /api/run/{run_id}/events
    SSE endpoint — поток событий выполнения.
    """
    run = run_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    async def event_generator():
        print(f"[SSE] Starting event stream for run {run_id}")
        async for event in run_manager.event_stream(run_id):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        print(f"[SSE] Event stream finished for run {run_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )