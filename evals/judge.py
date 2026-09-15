"""
LLM-судья для оценки качества ответов RAG-агента.
Только openai + httpx, никаких тяжёлых зависимостей.
"""
import os
import json
from pathlib import Path
from openai import OpenAI


# Цены gpt-4o-mini, $/1M токенов
PRICE_INPUT_PER_1M_USD = 0.15
PRICE_OUTPUT_PER_1M_USD = 0.60
USD_TO_RUB = 90.0


def _load_env():
    """Читает backend/.env, чтобы взять OPENAI_API_KEY и OPENAI_API_BASE."""
    env_path = Path(__file__).parent.parent / "backend" / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env()


JUDGE_PROMPT = """Ты — эксперт-судья качества ответов AI-системы.

Вопрос пользователя: {query}

Ответ AI-системы: {answer}

Критерии оценки:
{criteria}

Оцени ответ по шкале 0-10:
- 9-10: точно соответствует критериям, без ошибок
- 7-8: хороший ответ, есть мелкие упущения
- 4-6: частично верный, есть ошибки или пропуски
- 1-3: в основном неправильный
- 0: противоречит критериям, галлюцинация

Особенно строго проверяй пункты «НЕ должен»: если ответ содержит запрещённое — ставь 0-3.

Верни строго JSON:
{{"score": <число>, "reason": "<краткое обоснование на русском>"}}"""


def _make_client() -> OpenAI:
    """Создаёт OpenAI-клиент с учётом прокси из .env и таймаутом."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY не найден в backend/.env")

    base_url = os.getenv("OPENAI_API_BASE") or None
    if base_url:
        print(f"[judge] Using proxy: {base_url}", flush=True)

    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=30.0,
        max_retries=1,
    )


def _empty_usage() -> dict:
    return {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "cost_rub": 0.0}


def judge_answer(query: str, answer: str, criteria: str, model: str = "gpt-4o-mini") -> dict:
    """
    Оценивает ответ AI-системы по критериям.
    Возвращает {"score": int, "reason": str, "usage": {...}}.
    """
    if not answer:
        return {"score": 0, "reason": "Пустой ответ", "usage": _empty_usage()}

    client = _make_client()
    prompt = JUDGE_PROMPT.format(query=query, answer=answer, criteria=criteria)

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    # Считаем токены и стоимость
    usage_obj = resp.usage
    input_tokens = usage_obj.prompt_tokens if usage_obj else 0
    output_tokens = usage_obj.completion_tokens if usage_obj else 0
    cost_usd = (
        input_tokens / 1_000_000 * PRICE_INPUT_PER_1M_USD
        + output_tokens / 1_000_000 * PRICE_OUTPUT_PER_1M_USD
    )
    cost_rub = cost_usd * USD_TO_RUB
    usage = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
        "cost_rub": cost_rub,
    }

    content = resp.choices[0].message.content
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        return {
            "score": 0,
            "reason": f"Судья вернул невалидный JSON: {content[:200]}",
            "usage": usage,
        }

    score = int(result.get("score", 0))
    score = max(0, min(10, score))

    return {
        "score": score,
        "reason": result.get("reason", ""),
        "usage": usage,
    }
    
    
    
FAITHFULNESS_PROMPT = """Ты — эксперт-судья. Проверь, насколько ответ AI подтверждается предоставленным контекстом.

Контекст (фрагменты базы знаний):
{context}

Ответ AI:
{answer}

Задача:
1. Разбей ответ AI на отдельные утверждения (факты).
2. Для КАЖДОГО утверждения проверь — подтверждается ли оно контекстом.
3. Если утверждение — общая фраза («следует хранить бережно») — пропусти.
4. Если утверждение — конкретный факт (цифры, названия, условия) — проверь строго.

Верни строго JSON:
{{
  "claims": [
    {{"claim": "текст утверждения", "supported": true/false, "reason": "почему"}}
  ],
  "faithfulness_score": 0.0-1.0,
  "unsupported_count": <число выдуманных>
}}

faithfulness_score = подтверждённых / всего."""


def judge_faithfulness(question: str, answer: str, chunks: list[dict], model: str = "gpt-4o-mini") -> dict:
    """
    Оценивает, насколько ответ подтверждается контекстом (chunks).
    Возвращает {"score": 0.0-1.0, "unsupported": [...], "claims": [...], "usage": {...}}.
    """
    if not answer or not chunks:
        return {
            "score": 0.0,
            "unsupported": [],
            "claims": [],
            "usage": _empty_usage(),
        }

    # Собираем контекст из чанков (ограничим до 8 топовых)
    top = sorted(chunks, key=lambda c: c.get("score", 0), reverse=True)[:8]
    context = "\n\n".join(
        f"[{i+1}] {c.get('text', '')}"
        for i, c in enumerate(top)
    )

    client = _make_client()
    prompt = FAITHFULNESS_PROMPT.format(context=context, answer=answer)

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content
    usage_obj = resp.usage
    input_tokens = usage_obj.prompt_tokens if usage_obj else 0
    output_tokens = usage_obj.completion_tokens if usage_obj else 0
    cost_usd = (
        input_tokens / 1_000_000 * PRICE_INPUT_PER_1M_USD
        + output_tokens / 1_000_000 * PRICE_OUTPUT_PER_1M_USD
    )
    usage = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
        "cost_rub": cost_usd * USD_TO_RUB,
    }

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        return {"score": 0.0, "unsupported": [], "claims": [], "usage": usage}

    claims = result.get("claims", [])
    unsupported = [c for c in claims if not c.get("supported", True)]
    score = float(result.get("faithfulness_score", 0.0))
    score = max(0.0, min(1.0, score))

    return {
        "score": round(score, 3),
        "unsupported": unsupported,
        "claims": claims,
        "usage": usage,
    }