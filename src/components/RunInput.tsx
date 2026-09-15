interface RunInputProps {
  value: string;
  onChange: (value: string) => void;
  onRun: () => void;
  onStop: () => void;
  isRunning: boolean;
}

export function RunInput({
  value,
  onChange,
  onRun,
  onStop,
  isRunning,
}: RunInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onRun();
    }
  };

  return (
    <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-2xl p-4 shadow-xl">
      <label className="block text-sm font-medium text-slate-300 mb-2">
        Опишите задачу
      </label>
      <div className="flex gap-3">
        <textarea
          className="flex-1 bg-slate-900/80 border border-slate-600/50 rounded-xl px-4 py-3 text-white placeholder-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all"
          rows={2}
          placeholder="Например: проанализируй клиентов с проблемами оплаты..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isRunning}
        />
        <div className="flex flex-col gap-2">
          {!isRunning ? (
            <button
              onClick={onRun}
              disabled={!value.trim()}
              className="px-5 py-3 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/20 transition-all duration-200 flex items-center gap-2 whitespace-nowrap"
            >
              <span>▶</span> Запустить
            </button>
          ) : (
            <button
              onClick={onStop}
              className="px-5 py-3 bg-red-600 hover:bg-red-500 text-white font-semibold rounded-xl shadow-lg transition-all duration-200 flex items-center gap-2 whitespace-nowrap"
            >
              <span>⏹</span> Стоп
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
