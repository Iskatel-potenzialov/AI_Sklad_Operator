export function Header() {
  return (
    <header className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center text-xl font-bold shadow-lg shadow-emerald-500/20">
        📦
      </div>
      <div>
        <h1 className="text-xl font-bold tracking-tight">
          AI-оператор склада
        </h1>
        <p className="text-xs text-slate-400">
          Канцелярия • Управление запасами и поставщиками
        </p>
      </div>
    </header>
  );
}
