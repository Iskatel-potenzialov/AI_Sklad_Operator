"""
Админские endpoints: история прогонов evals + запуск прогона.
"""
import asyncio
import json
import os
import sqlite3
import subprocess
import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/admin", tags=["admin"])

DB_PATH = Path(__file__).parent.parent.parent / "data" / "app.db"


def _connect():
    """Открывает соединение с SQLite с row_factory для dict."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# Чтение прогонов
# ============================================================

@router.get("/evals")
async def list_eval_runs(limit: int = 50):
    """Список прогонов evals (последние сверху). Без results_json."""
    try:
        conn = _connect()
        try:
            cur = conn.execute("""
                SELECT id, timestamp, avg_score, passed, total_cases,
                       precision_5, recall_5, hit_5, mrr,
                       faithfulness_avg, faithfulness_unsupported,
                       backend_cost_rub, judge_cost_rub, faithfulness_cost_rub,
                       total_cost_rub, duration_sec
                FROM eval_runs
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

        return {"total": len(rows), "runs": rows}
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=500, detail=f"БД недоступна: {e}")


@router.get("/evals/latest")
async def get_latest_eval():
    """Последний прогон целиком."""
    try:
        conn = _connect()
        try:
            cur = conn.execute("SELECT id FROM eval_runs ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Прогонов нет")

        return await get_eval_run(row["id"])
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=500, detail=f"БД недоступна: {e}")


@router.get("/evals/{eval_id}")
async def get_eval_run(eval_id: int):
    """Полные детали одного прогона."""
    try:
        conn = _connect()
        try:
            cur = conn.execute(
                "SELECT * FROM eval_runs WHERE id = ?",
                (eval_id,)
            )
            row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Прогон не найден")

        data = dict(row)
        try:
            data["details"] = json.loads(data.pop("results_json"))
        except json.JSONDecodeError:
            data["details"] = None

        return data
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=500, detail=f"БД недоступна: {e}")


# ============================================================
# Запуск прогона evals
# ============================================================

class EvalJob:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = "running"
        self.output: list[str] = []
        self.exit_code: int | None = None
        self.subscribers: list[asyncio.Queue] = []

    def emit_threadsafe(self, event: dict):
        """Потокобезопасный emit — вызывается из фонового потока subprocess."""
        if event.get("type") == "line":
            self.output.append(event["text"])
        for q in list(self.subscribers):
            try:
                q.put_nowait(event)
            except Exception:
                pass

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self.subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self.subscribers:
            self.subscribers.remove(q)


_jobs: dict[str, EvalJob] = {}


def _run_eval_subprocess_sync(job: EvalJob, only: str | None):
    """Запускает evals/run.py в синхронном subprocess (в отдельном потоке)."""
    project_root = Path(__file__).parent.parent.parent
    python_exe = project_root / "evals_venv" / "Scripts" / "python.exe"

    if not python_exe.exists():
        job.emit_threadsafe({"type": "line", "text": f"❌ python не найден: {python_exe}"})
        job.status = "error"
        job.emit_threadsafe({"type": "done", "exit_code": -1})
        return

    args = [str(python_exe), "evals/run.py"]
    if only:
        args += ["--only", only]

    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

    try:
        proc = subprocess.Popen(
            args,
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except Exception as e:
        job.emit_threadsafe({"type": "line", "text": f"❌ Не удалось запустить: {e}"})
        job.status = "error"
        job.emit_threadsafe({"type": "done", "exit_code": -1})
        return

    try:
        for line in proc.stdout:
            job.emit_threadsafe({"type": "line", "text": line.rstrip()})
    except Exception as e:
        job.emit_threadsafe({"type": "line", "text": f"⚠ Ошибка чтения вывода: {e}"})

    exit_code = proc.wait()
    job.exit_code = exit_code
    job.status = "finished" if exit_code == 0 else "error"
    job.emit_threadsafe({"type": "done", "exit_code": exit_code})


@router.post("/evals/run")
async def run_evals(payload: dict | None = None):
    """Запускает evals/run.py в фоновом потоке. Возвращает job_id."""
    only = (payload or {}).get("only")
    job_id = str(uuid.uuid4())
    job = EvalJob(job_id)
    _jobs[job_id] = job

    thread = threading.Thread(
        target=_run_eval_subprocess_sync,
        args=(job, only),
        daemon=True,
    )
    thread.start()

    return {"job_id": job_id, "status": "running"}


@router.get("/evals/run/{job_id}/log")
async def stream_eval_log(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def gen():
        # 1. Уже накопленный вывод
        for line in job.output:
            yield f"data: {json.dumps({'type': 'line', 'text': line})}\n\n"

        if job.status != "running":
            yield f"data: {json.dumps({'type': 'done', 'exit_code': job.exit_code})}\n\n"
            return

        # 2. Новые события через очередь
        q = job.subscribe()
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=60)
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    continue
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get("type") == "done":
                    break
        finally:
            job.unsubscribe(q)

    return StreamingResponse(gen(), media_type="text/event-stream")