import { useRef, useState } from "react";

const API = "http://localhost:8000/api/admin";

interface RunEvalsButtonProps {
  onFinished?: () => void;
}

export function RunEvalsButton({ onFinished }: RunEvalsButtonProps) {
  const [running, setRunning] = useState(false);
  const [lines, setLines] = useState<string[]>([]);
  const [exitCode, setExitCode] = useState<number | null>(null);
  const [only, setOnly] = useState("");
  const logRef = useRef<HTMLDivElement>(null);

  const scrollDown = () => {
    setTimeout(() => {
      if (logRef.current) {
        logRef.current.scrollTop = logRef.current.scrollHeight;
      }
    }, 0);
  };

  const handleRun = async () => {
    if (running) return;
    setRunning(true);
    setLines([]);
    setExitCode(null);

    try {
      const body: any = {};
      if (only.trim()) body.only = only.trim();

      const r = await fetch(`${API}/evals/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const { job_id } = await r.json();

      const es = new EventSource(`${API}/evals/run/${job_id}/log`);
      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.type === "line") {
            setLines((prev) => [...prev, data.text]);
            scrollDown();
          } else if (data.type === "done") {
            setExitCode(data.exit_code);
            setRunning(false);
            es.close();
            onFinished?.();
          }
        } catch (err) {
          console.error("SSE parse error:", err);
        }
      };
      es.onerror = () => {
        setRunning(false);
        es.close();
      };
    } catch (e) {
      setLines((prev) => [...prev, `❌ Ошибка запуска: ${e}`]);
      setRunning(false);
    }
  };

  return (
    <div className="bg-slate-800/60 border border-slate-700/50 rounded-2xl p-5">
      <div className="flex items-center gap-3 mb-3">
        <button
          onClick={handleRun}
          disabled={running}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg text-sm"
        >
          {running ? "⏳ Идёт прогон..." : "▶ Запустить прогон evals"}
        </button>
        <input
          type="text"
          value={only}
          onChange={(e) => setOnly(e.target.value)}
          disabled={running}
          placeholder="--only (опционально): rag_002,rag_004"
          className="flex-1 bg-slate-900/80 border border-slate-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500"
        />
        {exitCode !== null && (
          <span className={exitCode === 0 ? "text-emerald-400 text-sm" : "text-red-400 text-sm"}>
            exit={exitCode}
          </span>
        )}
      </div>

      {lines.length > 0 && (
        <div
          ref={logRef}
          className="bg-slate-950 rounded-lg p-3 max-h-80 overflow-y-auto text-xs font-mono text-slate-300 whitespace-pre-wrap"
        >
          {lines.map((l, i) => (
            <div key={i}>{l}</div>
          ))}
        </div>
      )}
    </div>
  );
}