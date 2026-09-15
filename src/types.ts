/**
 * Типы событий SSE от backend.
 */
export interface SSEEvent {
  type:
    | "run_started"
    | "node_started"
    | "node_finished"
    | "assistant_message"
    | "tool_started"
    | "tool_finished"
    | "route_detected"
    | "action_pending"
    | "waiting_approval"
    | "action_resolved"
    | "error"
    | "run_finished"
    | "heartbeat";
  run_id?: string;
  node?: string;
  label?: string;
  tool?: string;
  intent?: string;
  content?: string;
  message?: string;
  answer?: string;
  success?: boolean;
  action?: {
    action_type: string;
    target_client_id?: string;
    target_supplier_id?: string;
    target_item_id?: string;      // ← добавить
    product_name?: string;        // ← добавить
    field?: string;
    old_value?: any;
    new_value?: any;
    description?: string;
    supplier_name?: string;
    items?: any[];
  };
  approved?: boolean;
}
