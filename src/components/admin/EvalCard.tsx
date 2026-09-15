interface EvalCardProps {
  label: string;
  value: string;
  suffix?: string;
}

export function EvalCard({ label, value, suffix }: EvalCardProps) {
  return (
    <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
      <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">
        {label}
      </div>
      <div className="text-2xl font-bold">
        {value}
        {suffix && <span className="text-sm text-slate-500 ml-1">{suffix}</span>}
      </div>
    </div>
  );
}