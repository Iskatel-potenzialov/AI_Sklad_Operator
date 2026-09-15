import type { SSEEvent } from "../types";

interface ActionApprovalProps {
  action: SSEEvent["action"];
  onApprove: () => void;
  onReject: () => void;
}

const ACTION_LABELS: Record<string, string> = {
  update_status: "Изменение статуса",
  update_debt: "Изменение долга",
  mark_inactive: "Пометка как неактивный",
  create_order: "Создание заказа",
  update_min_stock: "Изменение минимального остатка",
};

function CreateOrderDetails({ action }: { action: SSEEvent["action"] }) {
  if (!action) return null;
  return (
    <>
      <div className="flex justify-between">
        <span className="text-slate-400">Поставщик:</span>
        <span className="text-white font-mono">
          {action.supplier_name || action.target_supplier_id}
        </span>
      </div>

      {action.items && action.items.length > 0 && (
        <div className="mt-2 pt-2 border-t border-slate-700">
          <span className="text-slate-400 text-sm block mb-2">Товары:</span>
          <div className="space-y-1">
            {action.items.map((item, idx) => (
              <div key={idx} className="text-sm text-slate-300">
                • {item.product_name || item.item_id} — {item.quantity}{" "}
                {item.unit_of_measure}
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

function UpdateMinStockDetails({ action }: { action: SSEEvent["action"] }) {
  if (!action) return null;
  return (
    <>
      <div className="flex justify-between">
        <span className="text-slate-400">Товар:</span>
        <span className="text-white">
          {action.product_name || action.target_item_id}
        </span>
      </div>
      <div className="flex justify-between">
        <span className="text-slate-400">Было:</span>
        <span className="text-red-400">{String(action.old_value ?? "?")}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-slate-400">Станет:</span>
        <span className="text-emerald-400">
          {String(action.new_value ?? "?")}
        </span>
      </div>
    </>
  );
}

function GenericDetails({ action }: { action: SSEEvent["action"] }) {
  if (!action) return null;
  return (
    <>
      <div className="flex justify-between">
        <span className="text-slate-400">Объект:</span>
        <span className="text-white font-mono">
          {action.target_client_id ||
            action.target_supplier_id ||
            action.target_item_id ||
            "—"}
        </span>
      </div>

      {action.field && (
        <div className="flex justify-between">
          <span className="text-slate-400">Поле:</span>
          <span className="text-white">{action.field}</span>
        </div>
      )}

      {action.old_value !== undefined && (
        <div className="flex justify-between">
          <span className="text-slate-400">Было:</span>
          <span className="text-red-400">{String(action.old_value)}</span>
        </div>
      )}

      {action.new_value !== undefined && (
        <div className="flex justify-between">
          <span className="text-slate-400">Станет:</span>
          <span className="text-emerald-400">{String(action.new_value)}</span>
        </div>
      )}
    </>
  );
}

function renderDetails(action: SSEEvent["action"]) {
  if (!action) return null;

  switch (action.action_type) {
    case "create_order":
      return <CreateOrderDetails action={action} />;
    case "update_min_stock":
      return <UpdateMinStockDetails action={action} />;
    default:
      return <GenericDetails action={action} />;
  }
}

export function ActionApproval({
  action,
  onApprove,
  onReject,
}: ActionApprovalProps) {
  if (!action) return null;

  return (
    <div className="bg-amber-900/40 border border-amber-500/50 rounded-xl p-5 shadow-xl">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-2xl">⚠️</span>
        <h3 className="text-lg font-semibold text-amber-200">
          Требуется подтверждение
        </h3>
      </div>

      <div className="bg-slate-900/60 rounded-lg p-4 mb-4 space-y-2">
        <div className="flex justify-between">
          <span className="text-slate-400">Действие:</span>
          <span className="text-white font-medium">
            {ACTION_LABELS[action.action_type] || action.action_type}
          </span>
        </div>

        {renderDetails(action)}

        {action.description && (
          <div className="mt-2 pt-2 border-t border-slate-700">
            <span className="text-slate-400 text-sm">{action.description}</span>
          </div>
        )}
      </div>

      <div className="flex gap-3">
        <button
          onClick={onApprove}
          className="flex-1 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
        >
          <span>✓</span> Подтвердить
        </button>
        <button
          onClick={onReject}
          className="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-500 text-white font-semibold rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
        >
          <span>✗</span> Отклонить
        </button>
      </div>
    </div>
  );
}