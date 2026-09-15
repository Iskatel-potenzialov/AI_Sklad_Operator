interface Case {
  id: string;
  query: string;
  intent?: string;
  intent_ok?: boolean;
  answer?: string;
  score: number;
  reason: string;
  duration_sec?: number;
  faithfulness?: {
    score: number;
    unsupported: Array<{ claim: string; reason?: string }>;
  } | null;
  retrieval?: {
    "precision@5": number;
    "recall@5": number;
    mrr: number;
  } | null;
  retrieved_chunk_ids?: number[];
  expected_chunk_ids?: number[];
  error?: string;
}

interface EvalCaseListProps {
  cases: Case[];
}

function scoreColor(score: number): string {
  if (score >= 8) return "text-emerald-400";
  if (score >= 6) return "text-yellow-400";
  return "text-red-400";
}

export function EvalCaseList({ cases }: EvalCaseListProps) {
  if (!cases?.length) return <div className="text-slate-500 text-sm">Пусто</div>;

  return (
    <div className="space-y-3">
      {cases.map((c) => (
        <div
          key={c.id}
          className="bg-slate-900/60 border border-slate-700/50 rounded-lg p-4"
        >
          <div className="flex items-start justify-between gap-4 mb-2">
            <div className="flex-1">
              <div className="text-xs text-slate-500 font-mono">{c.id}</div>
              <div className="text-sm font-medium text-slate-200">
                {c.query}
              </div>
            </div>
            <div className={`text-2xl font-bold ${scoreColor(c.score)}`}>
              {c.score}
              <span className="text-xs text-slate-500 ml-1">/10</span>
            </div>
          </div>

          {c.error && (
            <div className="text-red-400 text-xs mb-2">Ошибка: {c.error}</div>
          )}

          {c.intent && (
            <div className="text-xs text-slate-400 mb-2">
              intent: <span className="font-mono">{c.intent}</span>
              {c.intent_ok === false && (
                <span className="text-red-400 ml-2">✗ не тот</span>
              )}
            </div>
          )}

          {c.retrieval && (
            <div className="text-xs text-slate-400 mb-2 font-mono">
              retrieval: P@5={c.retrieval["precision@5"]} R@5={c.retrieval["recall@5"]} MRR={c.retrieval.mrr}
              {c.retrieved_chunk_ids && (
                <span className="ml-2 text-slate-500">
                  found={JSON.stringify(c.retrieved_chunk_ids)}
                </span>
              )}
            </div>
          )}

          {c.faithfulness && (
            <div className="text-xs mb-2">
              <span className="text-slate-400">faithfulness: </span>
              <span className={c.faithfulness.score >= 0.8 ? "text-emerald-400" : "text-red-400"}>
                {c.faithfulness.score.toFixed(2)}
              </span>
              {c.faithfulness.unsupported?.length > 0 && (
                <span className="text-slate-500 ml-2">
                  ({c.faithfulness.unsupported.length} выдумано)
                </span>
              )}
            </div>
          )}

          <div className="text-xs text-slate-400 italic mb-2">
            {c.reason}
          </div>

          {c.faithfulness?.unsupported && c.faithfulness.unsupported.length > 0 && (
            <details className="text-xs text-slate-500 mt-2">
              <summary className="cursor-pointer hover:text-slate-300">
                Показать выдуманные утверждения
              </summary>
              <ul className="mt-2 space-y-1 pl-4">
                {c.faithfulness.unsupported.map((u, i) => (
                  <li key={i} className="text-red-300">
                    • «{u.claim}» {u.reason && <span className="text-slate-500">— {u.reason}</span>}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      ))}
    </div>
  );
}