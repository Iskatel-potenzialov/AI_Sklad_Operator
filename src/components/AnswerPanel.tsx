interface AnswerPanelProps {
  answer: string;
  isRunning: boolean;
}

export function AnswerPanel({ answer, isRunning }: AnswerPanelProps) {
  return (
    <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-2xl p-5 shadow-xl flex-1 min-h-[200px]">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">💬</span>
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Ответ AI
        </h2>
        {isRunning && (
          <span className="ml-auto flex items-center gap-1.5 text-xs text-emerald-400">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
            Обработка...
          </span>
        )}
      </div>

      <div className="text-slate-100 leading-relaxed whitespace-pre-wrap">
        {answer ? (
          <div className="animate-fade-in">{answer}</div>
        ) : isRunning ? (
          <div className="flex items-center gap-2 text-slate-500">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
            <span className="text-sm">AI думает...</span>
          </div>
        ) : (
          <div className="text-slate-500 text-sm italic">
            Здесь появится ответ AI после выполнения запроса
          </div>
        )}
      </div>
    </div>
  );
}
