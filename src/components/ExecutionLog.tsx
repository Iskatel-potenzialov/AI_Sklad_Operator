import type { SSEEvent } from "../types";

interface ExecutionLogProps {
  events: SSEEvent[];
}

function getEventIcon(type: string): string {
  switch (type) {
    case "run_started":
      return "🚀";
    case "node_started":
      return "⏳";
    case "node_finished":
      return "✅";
    case "assistant_message":
      return "💬";
    case "tool_started":
      return "🔧";
    case "tool_finished":
      return "🔧";
    case "route_detected":
      return "🔀";
    case "action_pending":
      return "⚠️";
    case "waiting_approval":
      return "⏸️";
    case "action_resolved":
      return "✓";
    case "error":
      return "❌";
    case "run_finished":
      return "🏁";
    case "heartbeat":
      return "💓";
    default:
      return "📌";
  }
}

function getEventLabel(event: SSEEvent): string {
  switch (event.type) {
    case "run_started":
      return "Запуск workflow";
    case "node_started":
      return event.label ? `${event.label}...` : `Узел: ${event.node}`;
    case "node_finished":
      return event.label ? `✓ ${event.label}` : `Завершён: ${event.node}`;
    case "assistant_message":
      return "Ответ LLM";
    case "tool_started":
      return event.tool || "tool";
    case "tool_finished": {
      const status = event.success ? "✓" : "✗";
      const msg = event.message || "";
      return `${event.tool}: ${status} ${msg}`;
    }
    case "route_detected":
      return `🔀 Маршрут: ${event.intent}`;
    case "action_pending":
      return `⚠️ Ожидается подтверждение действия`;
    case "waiting_approval":
      return `⏸️ ${event.message || "Ожидание подтверждения"}`;
    case "action_resolved":
      return event.approved ? `✓ Действие подтверждено` : `✗ Действие отклонено`;
    case "error":
      return `Ошибка: ${event.message}`;
    case "run_finished":
      return "Выполнение завершено";
    case "heartbeat":
      return "Heartbeat";
    default:
      return event.type;
  }
}

function getEventColor(type: string, success?: boolean): string {
  switch (type) {
    case "run_started":
      return "text-blue-400";
    case "node_started":
      return "text-yellow-400";
    case "node_finished":
      return "text-emerald-400";
    case "assistant_message":
      return "text-purple-400";
    case "tool_started":
      return "text-cyan-400";
    case "tool_finished":
      return success ? "text-emerald-400" : "text-red-400";
    case "route_detected":
      return "text-orange-400";
    case "action_pending":
      return "text-amber-400";
    case "waiting_approval":
      return "text-amber-400";
    case "action_resolved":
      return success ? "text-emerald-400" : "text-red-400";
    case "error":
      return "text-red-400";
    case "run_finished":
      return "text-emerald-400";
    default:
      return "text-slate-400";
  }
}

export function ExecutionLog({ events }: ExecutionLogProps) {
  // Фильтруем heartbeat из отображения
  const displayEvents = events.filter((e) => e.type !== "heartbeat");

  return (
    <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-2xl p-5 shadow-xl">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">📋</span>
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Выполнение
        </h2>
        {displayEvents.length > 0 && (
          <span className="ml-auto text-xs text-slate-500">
            {displayEvents.length} событий
          </span>
        )}
      </div>

      {/* Журнал событий */}
      <div className="space-y-1.5 max-h-[300px] overflow-y-auto">
        {displayEvents.length === 0 ? (
          <div className="text-slate-500 text-sm italic py-4 text-center">
            Журнал пуст — запустите задачу для отслеживания выполнения
          </div>
        ) : (
          displayEvents.map((event, index) => (
            <div
              key={index}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/40 text-sm ${getEventColor(event.type, event.success)}`}
            >
              <span className="text-xs">{getEventIcon(event.type)}</span>
              <span className="font-mono text-xs opacity-60">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span className="flex-1 truncate">{getEventLabel(event)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}