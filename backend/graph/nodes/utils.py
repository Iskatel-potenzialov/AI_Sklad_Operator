"""
Общие утилиты для узлов графа.
Аккумулирует токены и стоимость LLM-вызовов по run_id.
"""
import contextvars
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler
from backend.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_API_BASE


# Цены gpt-4o-mini, $/1M токенов
PRICE_INPUT_PER_1M_USD = 0.15
PRICE_OUTPUT_PER_1M_USD = 0.60
USD_TO_RUB = 90.0


# ContextVar — run_id для текущего контекста выполнения
_current_run_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_run_id", default=None
)

# Аккумулятор: {run_id: {input_tokens, output_tokens, cost_usd, cost_rub, calls}}
_run_costs: dict[str, dict] = {}


def set_current_run_id(run_id: str) -> None:
    """Устанавливает run_id для текущего выполнения. Вызывается в начале workflow."""
    _current_run_id.set(run_id)
    _run_costs.setdefault(run_id, {
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "cost_rub": 0.0,
        "calls": 0,
    })


def get_run_cost(run_id: str) -> dict:
    """Возвращает накопленную стоимость по run_id."""
    return _run_costs.get(run_id, {
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "cost_rub": 0.0,
        "calls": 0,
    })


class TokenUsageLogger(BaseCallbackHandler):
    """Логирует usage LLM и копит стоимость по run_id."""

    def on_llm_end(self, response, **kwargs):
        try:
            usage = self._extract_usage(response)
            if not usage:
                return

            input_tokens = usage.get("prompt_tokens") or 0
            output_tokens = usage.get("completion_tokens") or 0
            total_tokens = usage.get("total_tokens") or (input_tokens + output_tokens)

            cost_usd = (
                input_tokens / 1_000_000 * PRICE_INPUT_PER_1M_USD
                + output_tokens / 1_000_000 * PRICE_OUTPUT_PER_1M_USD
            )
            cost_rub = cost_usd * USD_TO_RUB

            # Лог в консоль (как было)
            print(
                f"[TOKENS] input={input_tokens} "
                f"output={output_tokens} "
                f"total={total_tokens} "
                f"cost=${cost_usd:.6f} "
                f"({cost_rub:.4f} ₽)"
            )

            # Аккумулируем по run_id
            run_id = _current_run_id.get()
            if run_id and run_id in _run_costs:
                _run_costs[run_id]["input_tokens"] += input_tokens
                _run_costs[run_id]["output_tokens"] += output_tokens
                _run_costs[run_id]["cost_usd"] += cost_usd
                _run_costs[run_id]["cost_rub"] += cost_rub
                _run_costs[run_id]["calls"] += 1

        except Exception as e:
            print(f"[TOKENS] error reading usage: {e}")

    @staticmethod
    def _extract_usage(response) -> dict | None:
        """Достаёт usage из ответа LLM."""
        llm_output = getattr(response, "llm_output", None)
        if llm_output:
            usage = llm_output.get("token_usage")
            if usage:
                return usage

        if response.generations:
            gen = response.generations[0][0]
            msg = getattr(gen, "message", None)
            if msg and getattr(msg, "usage_metadata", None):
                um = msg.usage_metadata
                return {
                    "prompt_tokens": um.get("input_tokens"),
                    "completion_tokens": um.get("output_tokens"),
                    "total_tokens": um.get("total_tokens"),
                }
        return None


def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    """Создаёт экземпляр LLM с логгером токенов."""
    kwargs = {
        "model": OPENAI_MODEL,
        "api_key": OPENAI_API_KEY,
        "temperature": temperature,
        "callbacks": [TokenUsageLogger()],
    }

    if OPENAI_API_BASE:
        kwargs["base_url"] = OPENAI_API_BASE
        print(f"[LLM] Using custom API base: {OPENAI_API_BASE}")

    return ChatOpenAI(**kwargs)