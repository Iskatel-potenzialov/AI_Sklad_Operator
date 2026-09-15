import { useEffect, useState } from "react";
import { EvalCard } from "../components/admin/EvalCard";
import { EvalTable } from "../components/admin/EvalTable";
import { EvalCaseList } from "../components/admin/EvalCaseList";
import { RunEvalsButton } from "../components/admin/RunEvalsButton";

const API = "http://localhost:8000/api/admin";

interface EvalRun {
  id: number;
  timestamp: string;
  avg_score: number;
  passed: number;
  total_cases: number;
  precision_5: number;
  recall_5: number;
  hit_5: number;
  mrr: number;
  faithfulness_avg: number;
  faithfulness_unsupported: number;
  total_cost_rub: number;
  duration_sec: number;
}

export default function Admin() {
  const [runs, setRuns] = useState<EvalRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [details, setDetails] = useState<any>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);

  const loadRuns = () => {
    setLoading(true);
    fetch(`${API}/evals`)
      .then((r) => r.json())
      .then((data) => {
        setRuns(data.runs || []);
        if (data.runs?.length) setSelectedRunId(data.runs[0].id);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadRuns();
  }, []);

  // Загрузка деталей выбранного прогона
  useEffect(() => {
    if (!selectedRunId) return;
    setDetailsLoading(true);
    fetch(`${API}/evals/${selectedRunId}`)
      .then((r) => r.json())
      .then((data) => setDetails(data))
      .catch((e) => console.error("details error:", e))
      .finally(() => setDetailsLoading(false));
  }, [selectedRunId]);

  const latest = runs[0];
  const cases = details?.details?.results || [];

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <header className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Evals Admin</h1>
            <p className="text-slate-400 text-sm mt-1">
              История прогонов качества RAG-агента
            </p>
          </div>
          <a
            href="/"
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm"
          >
            ← К основному
          </a>
        </header>

        {/* Кнопка запуска — всегда видна */}
        <section className="mb-6">
          <RunEvalsButton onFinished={loadRuns} />
        </section>

        {loading && <div className="text-slate-400">Загрузка...</div>}
        {error && <div className="text-red-400">Ошибка: {error}</div>}

        {latest && (
          <>
            <section className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
              <EvalCard label="Avg score" value={`${latest.avg_score}`} suffix="/10" />
              <EvalCard label="Passed" value={`${latest.passed}`} suffix={`/${latest.total_cases}`} />
              <EvalCard label="Recall@5" value={latest.recall_5.toFixed(3)} />
              <EvalCard label="Faithfulness" value={latest.faithfulness_avg.toFixed(3)} />
              <EvalCard label="Стоимость" value={latest.total_cost_rub.toFixed(2)} suffix="₽" />
              <EvalCard label="Время" value={String(Math.round(latest.duration_sec))} suffix="сек" />
            </section>

            <section className="bg-slate-800/60 rounded-2xl p-5 mb-6">
              <h2 className="text-lg font-semibold mb-3">История прогонов</h2>
              <EvalTable
                runs={runs}
                selectedId={selectedRunId}
                onSelect={setSelectedRunId}
              />
            </section>

            {selectedRunId && (
              <section className="bg-slate-800/60 rounded-2xl p-5">
                <h2 className="text-lg font-semibold mb-3">
                  Кейсы прогона #{selectedRunId}
                  {detailsLoading && <span className="text-slate-500 text-sm ml-2">загрузка...</span>}
                </h2>
                {!detailsLoading && <EvalCaseList cases={cases} />}
              </section>
            )}
          </>
        )}

        {!loading && !latest && (
          <div className="text-slate-400">
            Прогонов пока нет. Нажми «Запустить прогон evals» выше.
          </div>
        )}
      </div>
    </div>
  );
}