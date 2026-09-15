"""
Прогон golden set через backend + LLM-судья + retrieval-метрики + Faithfulness + стоимость.
Запуск: python evals/run.py (из E:\\mcp)
"""
import json
import time
from pathlib import Path

import httpx

from judge import judge_answer, judge_faithfulness
from retrieval_metrics import compute_all


import sqlite3
import sys

from datetime import datetime



BACKEND_URL = "http://localhost:8000"
EVALS_DIR = Path(__file__).parent
GOLDEN = EVALS_DIR / "golden_set.jsonl"
RESULTS = EVALS_DIR / "results.json"
TIMEOUT = 180.0
RETRIEVAL_K = 5
DB_PATH = Path(__file__).parent.parent / "data" / "app.db"


def _load_cases() -> list[dict]:
    lines = GOLDEN.read_text(encoding="utf-8").splitlines()
    cases = [json.loads(l) for l in lines if l.strip()]

    only = None
    for i, arg in enumerate(sys.argv):
        if arg == "--only" and i + 1 < len(sys.argv):
            only = sys.argv[i + 1].split(",")
            break

    if only:
        cases = [c for c in cases if c["id"] in only]
        print(f"[--only] Отфильтровано: {[c['id'] for c in cases]}")

    return cases


def run_case(case: dict) -> dict:
    """Отправляет запрос в backend, слушает SSE, собирает intent, answer, chunk_ids, chunks, backend_cost."""
    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.post(f"{BACKEND_URL}/api/run", json={"request": case["query"]})
        r.raise_for_status()
        run_id = r.json()["run_id"]

        intent = None
        answer = None
        chunk_ids: list[int] = []
        chunks: list[dict] = []
        backend_cost = None
        finished = False

        try:
            with client.stream("GET", f"{BACKEND_URL}/api/run/{run_id}/events") as stream:
                for line in stream.iter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        event = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue

                    etype = event.get("type")

                    if etype == "route_detected":
                        intent = event.get("intent")
                    elif etype == "assistant_message":
                        answer = event.get("content")
                    elif etype == "retrieval_done":
                        # chunk_ids — накапливаем уникальные
                        for cid in event.get("chunk_ids", []):
                            if cid not in chunk_ids:
                                chunk_ids.append(cid)
                        # chunks — НАКАПЛИВАЕМ, не перезаписываем
                        new_chunks = event.get("chunks", [])
                        if new_chunks:
                            existing_ids = {c.get("chunk_id") for c in chunks}
                            for c in new_chunks:
                                if c.get("chunk_id") not in existing_ids:
                                    chunks.append(c)
                                    existing_ids.add(c.get("chunk_id"))
                    elif etype == "run_finished":
                        if event.get("answer") and not answer:
                            answer = event["answer"]
                        backend_cost = event.get("backend_cost")
                        finished = True
                        break
                    elif etype == "error":
                        answer = f"ERROR: {event.get('message')}"
                        backend_cost = event.get("backend_cost")
                        finished = True
                        break
        except httpx.ReadTimeout:
            print(f"⚠ timeout", end=" ")

        if not finished:
            print(f"⚠ SSE закрыт без run_finished", end=" ")

        return {
            "intent": intent,
            "answer": answer,
            "chunk_ids": chunk_ids,
            "chunks": chunks,
            "backend_cost": backend_cost,
        }


def save_eval_run(results_dict: dict, duration_sec: float) -> int:
    """Сохраняет прогон в eval_runs. Возвращает id записи."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO eval_runs (
                timestamp, avg_score, passed, total_cases,
                precision_5, recall_5, hit_5, mrr,
                faithfulness_avg, faithfulness_unsupported,
                backend_cost_rub, judge_cost_rub, faithfulness_cost_rub, total_cost_rub,
                duration_sec, results_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            results_dict["avg_score"],
            results_dict["passed"],
            results_dict["total_cases"],
            results_dict["retrieval_avg"]["precision@5"],
            results_dict["retrieval_avg"]["recall@5"],
            results_dict["retrieval_avg"]["hit@5"],
            results_dict["retrieval_avg"]["mrr"],
            results_dict.get("faithfulness_avg", 0.0),
            results_dict.get("faithfulness_unsupported_total", 0),
            results_dict["backend_totals"]["cost_rub"],
            results_dict["judge_totals"]["cost_rub"],
            results_dict["faithfulness_totals"]["cost_rub"],
            results_dict["grand_total_rub"],
            round(duration_sec, 2),
            json.dumps(results_dict, ensure_ascii=False),
        ))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()



def main():
    run_started_at = time.time()
    cases = _load_cases()
    print(f"=== Прогон {len(cases)} кейсов ===\n")

    results = []
    total_score = 0

    # Судья
    total_judge_in = 0
    total_judge_out = 0
    total_judge_cost_rub = 0.0

    # Faithfulness
    total_faith_in = 0
    total_faith_out = 0
    total_faith_cost_rub = 0.0

    # Backend
    total_backend_in = 0
    total_backend_out = 0
    total_backend_cost_rub = 0.0

    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case['query']}")
        print(f"     отправляю...", end=" ", flush=True)
        t0 = time.time()

        try:
            run_result = run_case(case)
            elapsed = time.time() - t0
            print(f"ответ ({elapsed:.0f}s), оцениваю...", end=" ", flush=True)

            intent_ok = run_result["intent"] == case["expected_intent"]

            retrieval = None
            if case.get("expected_chunk_ids"):
                retrieval = compute_all(
                    expected=case["expected_chunk_ids"],
                    retrieved=run_result.get("chunk_ids", []),
                    k=RETRIEVAL_K,
                )

            backend_cost = run_result.get("backend_cost") or {}
            backend_cost_rub = backend_cost.get("cost_rub", 0.0)
            total_backend_cost_rub += backend_cost_rub
            total_backend_in += backend_cost.get("input_tokens", 0)
            total_backend_out += backend_cost.get("output_tokens", 0)

            judge_usage = {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "cost_rub": 0.0}

            if case["type"] == "llm_judge":
                judgment = judge_answer(case["query"], run_result["answer"], case["criteria"])
                score = judgment["score"]
                reason = judgment["reason"]
                judge_usage = judgment.get("usage", judge_usage)
            else:
                score = 10 if intent_ok else 0
                reason = "intent OK" if intent_ok else (
                    f"intent: ожидался {case['expected_intent']}, получен {run_result['intent']}"
                )

            faithfulness_result = None
            faith_usage = {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "cost_rub": 0.0}
            if case["type"] == "llm_judge" and run_result.get("chunks"):
                faithfulness_result = judge_faithfulness(
                    case["query"],
                    run_result["answer"],
                    run_result["chunks"],
                )
                faith_usage = faithfulness_result.get("usage", faith_usage)
                total_faith_in += faith_usage["input_tokens"]
                total_faith_out += faith_usage["output_tokens"]
                total_faith_cost_rub += faith_usage.get("cost_rub", 0.0)

            total_score += score
            total_judge_in += judge_usage["input_tokens"]
            total_judge_out += judge_usage["output_tokens"]
            total_judge_cost_rub += judge_usage.get("cost_rub", 0.0)

            results.append({
                "id": case["id"],
                "query": case["query"],
                "intent": run_result["intent"],
                "intent_ok": intent_ok,
                "answer": run_result["answer"],
                "score": score,
                "reason": reason,
                "duration_sec": round(elapsed, 2),
                "judge_usage": judge_usage,
                "faithfulness": faithfulness_result,
                "faithfulness_usage": faith_usage,
                "backend_cost": backend_cost,
                "retrieved_chunk_ids": run_result.get("chunk_ids", []),
                "expected_chunk_ids": case.get("expected_chunk_ids", []),
                "retrieval": retrieval,
            })

            status = "✓" if score >= 7 else "✗"
            per_case_cost = (
                judge_usage.get("cost_usd", 0)
                + faith_usage.get("cost_usd", 0)
                + backend_cost_rub / 90
            )
            print(f"\n  {status} intent={run_result['intent']} score={score}/10 cost=${per_case_cost:.5f}")

            if retrieval:
                print(f"    retrieval: P@5={retrieval['precision@5']} "
                      f"R@5={retrieval['recall@5']} "
                      f"MRR={retrieval['mrr']} "
                      f"| found={run_result.get('chunk_ids', [])} "
                      f"expected={case.get('expected_chunk_ids', [])}")

            if faithfulness_result:
                faith = faithfulness_result["score"]
                unsup = faithfulness_result.get("unsupported", [])
                print(f"    faithfulness: {faith:.2f} ({len(unsup)} выдумано)")

            print(f"    {reason}\n")

        except Exception as e:
            print(f"\n  ✗ Ошибка: {e}\n")
            results.append({
                "id": case["id"],
                "query": case["query"],
                "error": str(e),
                "score": 0,
            })

    # Итоговые расчёты
    avg = total_score / len(cases) if cases else 0
    passed = sum(1 for r in results if r.get("score", 0) >= 7)

    judge_cost_usd = total_judge_cost_rub / 90.0
    faith_cost_usd = total_faith_cost_rub / 90.0
    backend_cost_usd = total_backend_cost_rub / 90.0
    grand_total_rub = total_judge_cost_rub + total_faith_cost_rub + total_backend_cost_rub
    grand_total_usd = grand_total_rub / 90.0

    retrieval_results = [r["retrieval"] for r in results if r.get("retrieval")]
    if retrieval_results:
        avg_p = sum(r["precision@5"] for r in retrieval_results) / len(retrieval_results)
        avg_r = sum(r["recall@5"] for r in retrieval_results) / len(retrieval_results)
        avg_hit = sum(r["hit@5"] for r in retrieval_results) / len(retrieval_results)
        avg_mrr = sum(r["mrr"] for r in retrieval_results) / len(retrieval_results)
    else:
        avg_p = avg_r = avg_hit = avg_mrr = 0.0

    faith_results = [r["faithfulness"] for r in results if r.get("faithfulness")]
    if faith_results:
        avg_faith = sum(f["score"] for f in faith_results) / len(faith_results)
        total_unsup = sum(len(f.get("unsupported", [])) for f in faith_results)
    else:
        avg_faith = 0.0
        total_unsup = 0

    # Итоговый вывод
    print(f"{'=' * 60}")
    print(f"ИТОГО: средняя оценка {avg:.1f}/10")
    print(f"Кейсов: {len(cases)}, пройдено (>=7): {passed}")
    print(f"{'-' * 60}")
    print(f"Retrieval (детерминированные метрики):")
    print(f"  Precision@5: {avg_p:.3f}")
    print(f"  Recall@5:    {avg_r:.3f}")
    print(f"  Hit@5:       {avg_hit:.3f}")
    print(f"  MRR:         {avg_mrr:.3f}")
    print(f"{'-' * 60}")
    print(f"Faithfulness (галлюцинации):")
    print(f"  Средний score: {avg_faith:.3f}  (1.0 = всё подтверждено)")
    print(f"  Выдуманных:    {total_unsup}")
    print(f"{'-' * 60}")
    print(f"Backend (агент + все узлы):")
    print(f"  Input tokens:  {total_backend_in:,}")
    print(f"  Output tokens: {total_backend_out:,}")
    print(f"  Стоимость:     ${backend_cost_usd:.5f} ({total_backend_cost_rub:.4f} ₽)")
    print(f"{'-' * 60}")
    print(f"Судья (LLM-as-judge):")
    print(f"  Вызовов:       {len(cases)}")
    print(f"  Input tokens:  {total_judge_in:,}")
    print(f"  Output tokens: {total_judge_out:,}")
    print(f"  Стоимость:     ${judge_cost_usd:.5f} ({total_judge_cost_rub:.4f} ₽)")
    print(f"{'-' * 60}")
    print(f"Faithfulness-судья:")
    print(f"  Input tokens:  {total_faith_in:,}")
    print(f"  Output tokens: {total_faith_out:,}")
    print(f"  Стоимость:     ${faith_cost_usd:.5f} ({total_faith_cost_rub:.4f} ₽)")
    print(f"{'-' * 60}")
    print(f"ИТОГО СТОИМОСТЬ ПРОГОНА: {grand_total_rub:.4f} ₽ (${grand_total_usd:.5f})")
    print(f"{'=' * 60}\n")

    # Собираем полный results_dict
    results_dict = {
        "avg_score": round(avg, 2),
        "total_cases": len(cases),
        "passed": passed,
        "retrieval_avg": {
            "precision@5": round(avg_p, 3),
            "recall@5": round(avg_r, 3),
            "hit@5": round(avg_hit, 3),
            "mrr": round(avg_mrr, 3),
        },
        "faithfulness_avg": round(avg_faith, 3),
        "faithfulness_unsupported_total": total_unsup,
        "backend_totals": {
            "input_tokens": total_backend_in,
            "output_tokens": total_backend_out,
            "cost_usd": round(backend_cost_usd, 6),
            "cost_rub": round(total_backend_cost_rub, 4),
        },
        "judge_totals": {
            "input_tokens": total_judge_in,
            "output_tokens": total_judge_out,
            "cost_usd": round(judge_cost_usd, 6),
            "cost_rub": round(total_judge_cost_rub, 4),
        },
        "faithfulness_totals": {
            "input_tokens": total_faith_in,
            "output_tokens": total_faith_out,
            "cost_usd": round(faith_cost_usd, 6),
            "cost_rub": round(total_faith_cost_rub, 4),
        },
        "grand_total_rub": round(grand_total_rub, 4),
        "grand_total_usd": round(grand_total_usd, 6),
        "results": results,
    }

    # Сохранение в JSON
    RESULTS.write_text(
        json.dumps(results_dict, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Результаты сохранены: {RESULTS}")

    # Сохранение в БД
    total_duration = time.time() - run_started_at
    try:
        eval_id = save_eval_run(results_dict, total_duration)
        print(f"Прогон сохранён в БД: id={eval_id}")
    except Exception as e:
        print(f"⚠ Не удалось сохранить в БД: {e}")


if __name__ == "__main__":
    main()