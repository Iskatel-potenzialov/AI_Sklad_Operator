interface Run {
  id: number;
  timestamp: string;
  avg_score: number;
  passed: number;
  total_cases: number;
  recall_5: number;
  faithfulness_avg: number;
  total_cost_rub: number;
  duration_sec: number;
}

interface EvalTableProps {
  runs: Run[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function EvalTable({ runs, selectedId, onSelect }: EvalTableProps) {
  if (!runs.length) return <div className="text-slate-500 text-sm">Пусто</div>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-slate-400 text-left border-b border-slate-700">
            <th className="pb-2 px-2">#</th>
            <th className="pb-2 px-2">Дата</th>
            <th className="pb-2 px-2">Score</th>
            <th className="pb-2 px-2">Passed</th>
            <th className="pb-2 px-2">Recall@5</th>
            <th className="pb-2 px-2">Faithful</th>
            <th className="pb-2 px-2">Cost</th>
            <th className="pb-2 px-2">Время</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((r) => (
            <tr
              key={r.id}
              onClick={() => onSelect(r.id)}
              className={`cursor-pointer border-b border-slate-800 hover:bg-slate-700/30 ${
                selectedId === r.id ? "bg-slate-700/40" : ""
              }`}
            >
              <td className="py-2 px-2 text-slate-500">{r.id}</td>
              <td className="py-2 px-2">{formatDate(r.timestamp)}</td>
              <td className="py-2 px-2 font-mono">{r.avg_score}</td>
              <td className="py-2 px-2 font-mono">
                {r.passed}/{r.total_cases}
              </td>
              <td className="py-2 px-2 font-mono">{r.recall_5.toFixed(3)}</td>
              <td className="py-2 px-2 font-mono">{r.faithfulness_avg.toFixed(3)}</td>
              <td className="py-2 px-2 font-mono">{r.total_cost_rub.toFixed(2)} ₽</td>
              <td className="py-2 px-2 font-mono">{Math.round(r.duration_sec)}s</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}