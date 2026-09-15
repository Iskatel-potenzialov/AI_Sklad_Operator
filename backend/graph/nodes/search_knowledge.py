"""
Узел: search_knowledge (RAG-агент)

Логика:
  LLM в цикле выбирает tools:
    - search_documents(query)          — искать как есть
    - reformulate_and_search(query)    — LLM переформулирует и ищет снова
    - evaluate_relevance(question)     — LLM оценивает, достаточно ли чанков

  Цикл идёт до:
    - LLM перестаёт вызывать tool → генерирует финальный ответ
    - 2 evaluate подряд вернули "недостаточно" → fallback
    - достигнут MAX_ITERATIONS → fallback
"""
import json
import httpx
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from backend.graph.state import GraphState
from backend.graph.nodes.utils import get_llm
from backend.config import RAG_SERVICE_URL, QDRANT_URL, QDRANT_COLLECTION


MAX_ITERATIONS = 5
TOP_K = 3
SCORE_THRESHOLD = 0.60
MAX_CONSECUTIVE_INSUFFICIENT = 2


# ============================================================
# Низкоуровневые операции
# ============================================================

def _embed(text: str) -> list[float]:
    resp = httpx.post(
        f"{RAG_SERVICE_URL}/embed",
        json={"text": text},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["vector"]


def _qdrant_search(vector: list[float], top_k: int = TOP_K) -> list[dict]:
    resp = httpx.post(
        f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/query",
        json={"query": vector, "limit": top_k, "with_payload": True},
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()

    result = data.get("result", {})
    points = result.get("points", []) if isinstance(result, dict) else result

    chunks = []
    for p in points:
        pl = p.get("payload", {})
        chunks.append({
            "score": round(p.get("score", 0.0), 4),
            "text": pl.get("text", ""),
            "chunk_id": pl.get("chunk_id"),
        })
    return chunks


def _search_internal(query: str) -> list[dict]:
    """Поиск + фильтр по threshold."""
    vec = _embed(query)
    hits = _qdrant_search(vec, TOP_K)
    good = [c for c in hits if c["score"] >= SCORE_THRESHOLD]
    print(f"[search_knowledge]   query='{query}' → {len(good)}/{len(hits)} above {SCORE_THRESHOLD}")
    for c in good:
        print(f"[search_knowledge]     score={c['score']} chunk_id={c['chunk_id']}")
    return good


def _dedupe(chunks: list[dict]) -> list[dict]:
    """Убирает дубли по chunk_id, сохраняет порядок."""
    seen = set()
    out = []
    for c in chunks:
        cid = c.get("chunk_id")
        if cid in seen:
            continue
        seen.add(cid)
        out.append(c)
    return out


def _chunk_ids(chunks: list[dict]) -> list[int]:
    """Извлекает chunk_id из списка чанков."""
    return [c["chunk_id"] for c in chunks]


# ============================================================
# Реализация tools
# ============================================================

def _run_search_documents(query: str) -> tuple[str, list[dict]]:
    """Tool 1: искать как есть."""
    print(f"[search_knowledge] [tool] search_documents('{query}')")
    chunks = _search_internal(query)
    return f"Найдено {len(chunks)} релевантных чанков", chunks


def _run_reformulate_and_search(query: str) -> tuple[str, list[dict], str]:
    """Tool 2: LLM переформулирует запрос, потом ищет."""
    print(f"[search_knowledge] [tool] reformulate_and_search('{query}')")
    llm = get_llm(temperature=0.3)
    prompt = (
        "Переформулируй запрос так, чтобы он лучше подходил для поиска "
        "в базе знаний склада канцелярии. Верни ТОЛЬКО новую формулировку, "
        "без пояснений и кавычек.\n\n"
        f"Исходный запрос: {query}"
    )
    resp = llm.invoke([HumanMessage(content=prompt)])
    new_query = resp.content.strip().strip('"').strip("'").split("\n")[0]
    print(f"[search_knowledge]   reformulated → '{new_query}'")

    chunks = _search_internal(new_query)
    return f"Переформулировано в '{new_query}', найдено {len(chunks)} чанков", chunks, new_query


def _run_evaluate_relevance(question: str, all_chunks: list[dict]) -> dict:
    """Tool 3: LLM оценивает, достаточно ли чанков."""
    print(f"[search_knowledge] [tool] evaluate_relevance('{question[:60]}...')")

    if not all_chunks:
        return {"sufficient": False, "missing": "Ничего не найдено"}

    top = sorted(all_chunks, key=lambda c: c["score"], reverse=True)[:8]
    context = "\n\n".join(
        f"[{i+1}] (score={c['score']})\n{c['text'][:500]}"
        for i, c in enumerate(top)
    )

    llm = get_llm(temperature=0.1)
    prompt = f"""Вопрос пользователя: {question}

Найденный контекст:
{context}

Оцени, достаточно ли контекста для содержательного ответа на вопрос.

Правила:
- sufficient=true, если в контексте есть ХОТЯ БЫ ОСНОВНАЯ информация по теме вопроса.
  Не требуй покрытия всех деталей и подтем.
- sufficient=false ТОЛЬКО если:
  * контекст совсем не по теме, или
  * ответить невозможно из-за отсутствия ключевой информации.

Примеры:
- Вопрос про температуру хранения → в контексте есть температурный диапазон → true
  (даже если нет влажности — этого достаточно)
- Вопрос про правила хранения клея → в контексте только про бумагу → false

Верни строго JSON:
{{"sufficient": true/false, "missing": "что именно не хватает (только если false, иначе пустая строка)"}}
"""
    resp = llm.invoke([HumanMessage(content=prompt)])
    content = resp.content.strip()

    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    try:
        verdict = json.loads(content)
    except json.JSONDecodeError:
        print(f"[search_knowledge]   evaluate: bad JSON → defaulting to sufficient=True")
        verdict = {"sufficient": True, "missing": ""}

    print(f"[search_knowledge]   evaluate verdict: sufficient={verdict.get('sufficient')}, "
          f"missing={verdict.get('missing', '')!r}")
    return verdict


def _generate_final_answer(question: str, chunks: list[dict], fallback: bool = False) -> str:
    """Финальный ответ LLM по накопленным чанкам."""
    top = sorted(chunks, key=lambda c: c["score"], reverse=True)[:8]
    context = "\n\n".join(
        f"[{i+1}] (score={c['score']})\n{c['text']}"
        for i, c in enumerate(top)
    )

    system = (
        "Ты — AI-ассистент склада канцелярии.\n"
        "Отвечай ТОЛЬКО на основе контекста. Если чего-то нет — так и скажи.\n"
        "Не выдумывай факты. Отвечай по-русски, кратко и по делу."
    )
    if fallback:
        system += (
            "\n\nВАЖНО: было сделано несколько попыток поиска, но контекст "
            "может быть неполным. В начале ответа отметь это одной фразой."
        )

    llm = get_llm(temperature=0.2)
    resp = llm.invoke([
        SystemMessage(content=system),
        HumanMessage(content=f"Контекст:\n{context}\n\nВопрос: {question}"),
    ])
    return resp.content


# ============================================================
# Описание tools для LLM
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": (
                "Найти релевантные чанки в базе знаний по запросу. "
                "Используй, когда запрос пользователя уже хорошо сформулирован."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Поисковый запрос"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reformulate_and_search",
            "description": (
                "Переформулировать запрос и снова поискать. "
                "Используй, если предыдущий поиск дал мало результатов "
                "или ничего по теме."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Исходный запрос, который надо переформулировать"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_relevance",
            "description": (
                "Проверить, достаточно ли уже найденного контекста для ответа. "
                "Вызывай после поиска, чтобы понять, нужен ли ещё один запрос."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Вопрос пользователя"}
                },
                "required": ["question"],
            },
        },
    },
]


SYSTEM_PROMPT = """Ты — RAG-агент склада канцелярии.
У тебя есть база знаний (нормы, регламенты, инструкции).

Работай по плану:
1. Начни с search_documents — попробуй найти по запросу как есть.
2. После поиска вызови evaluate_relevance и посмотри, достаточно ли контекста.
3. Если нет — вызови reformulate_and_search с более точной формулировкой.
4. Повторяй п.2-3, пока контекст не станет достаточным.
5. Когда достаточно — прекрати вызывать tools и сгенерируй финальный ответ.

Правила:
- Не вызывай tools без нужды.
- Если после 3-4 попыток ничего не нашёл — прекрати и ответь честно.
- Отвечай на русском."""


# ============================================================
# Главный узел
# ============================================================

def search_knowledge(state: GraphState) -> dict:
    print(f"[search_knowledge] === RAG AGENT START ===")
    print(f"[search_knowledge] Query: {state.user_request}")

    llm = get_llm(temperature=0.2)
    llm_with_tools = llm.bind_tools(TOOLS)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=state.user_request),
    ]
    accumulated: list[dict] = []
    tool_trace: list[str] = []
    consecutive_insufficient = 0

    try:
        for iteration in range(1, MAX_ITERATIONS + 1):
            print(f"[search_knowledge] --- Iteration {iteration}/{MAX_ITERATIONS} ---")

            response = llm_with_tools.invoke(messages)
            messages.append(response)

            # LLM не вызывает tools → финальный ответ
            if not response.tool_calls:
                print(f"[search_knowledge] LLM finished, no tool calls → final answer")
                return {
                    "answer": response.content,
                    "tool_trace": tool_trace,
                    "retrieved_chunk_ids": _chunk_ids(accumulated),
                    "retrieved_chunks": accumulated,
                    "route_trace": state.route_trace + [
                        f"search_knowledge: agent done, {iteration} iterations, "
                        f"{len(accumulated)} chunks"
                    ],
                }

            # Обрабатываем каждый tool_call
            for call in response.tool_calls:
                name = call["name"]
                args = call["args"]
                call_id = call["id"]

                if name == "search_documents":
                    summary, chunks = _run_search_documents(args["query"])
                    accumulated.extend(chunks)
                    accumulated = _dedupe(accumulated)
                    tool_trace.append(
                        f"🔍 search_documents('{args['query']}') → {len(chunks)} чанков "
                        f"| chunk_ids={_chunk_ids(chunks)}"
                    )
                    messages.append(ToolMessage(
                        content=json.dumps({
                            "summary": summary,
                            "chunks_count": len(chunks),
                            "accumulated": len(accumulated),
                        }, ensure_ascii=False),
                        tool_call_id=call_id,
                    ))

                elif name == "reformulate_and_search":
                    summary, chunks, new_q = _run_reformulate_and_search(args["query"])
                    accumulated.extend(chunks)
                    accumulated = _dedupe(accumulated)
                    tool_trace.append(
                        f"✏️ reformulate_and_search → '{new_q}' → {len(chunks)} чанков "
                        f"| chunk_ids={_chunk_ids(chunks)}"
                    )
                    messages.append(ToolMessage(
                        content=json.dumps({
                            "summary": summary,
                            "new_query": new_q,
                            "chunks_count": len(chunks),
                            "accumulated": len(accumulated),
                        }, ensure_ascii=False),
                        tool_call_id=call_id,
                    ))

                elif name == "evaluate_relevance":
                    verdict = _run_evaluate_relevance(args["question"], accumulated)
                    verdict_label = "достаточно" if verdict.get("sufficient") else "недостаточно"
                    tool_trace.append(
                        f"🧠 evaluate_relevance → {verdict_label}"
                    )
                    messages.append(ToolMessage(
                        content=json.dumps(verdict, ensure_ascii=False),
                        tool_call_id=call_id,
                    ))

                    # Счётчик подряд идущих "недостаточно"
                    if verdict.get("sufficient"):
                        consecutive_insufficient = 0
                    else:
                        consecutive_insufficient += 1
                        if consecutive_insufficient >= MAX_CONSECUTIVE_INSUFFICIENT:
                            print(
                                f"[search_knowledge] {MAX_CONSECUTIVE_INSUFFICIENT} "
                                f"insufficient evaluations in a row → forcing fallback answer"
                            )
                            tool_trace.append(
                                f"⚠️ {MAX_CONSECUTIVE_INSUFFICIENT} оценки подряд: "
                                f"недостаточно → ответ по лучшим чанкам"
                            )
                            if accumulated:
                                answer = _generate_final_answer(
                                    state.user_request, accumulated, fallback=True
                                )
                            else:
                                answer = "В базе знаний нет информации по этому вопросу."
                            return {
                                "answer": answer,
                                "tool_trace": tool_trace,
                                "retrieved_chunk_ids": _chunk_ids(accumulated),
                                "retrieved_chunks": accumulated,
                                "route_trace": state.route_trace + [
                                    f"search_knowledge: {MAX_CONSECUTIVE_INSUFFICIENT} "
                                    f"consecutive insufficient, "
                                    f"{len(accumulated)} chunks (fallback)"
                                ],
                            }

                else:
                    tool_trace.append(f"❓ неизвестный tool: {name}")
                    messages.append(ToolMessage(
                        content=json.dumps({"error": f"unknown tool {name}"}),
                        tool_call_id=call_id,
                    ))

        # Достигли MAX_ITERATIONS — fallback
        print(f"[search_knowledge] MAX_ITERATIONS ({MAX_ITERATIONS}) reached, generating fallback answer")
        tool_trace.append(f"⚠️ достигнут лимит {MAX_ITERATIONS} итераций → fallback")
        if accumulated:
            answer = _generate_final_answer(state.user_request, accumulated, fallback=True)
        else:
            answer = "В базе знаний нет информации по этому вопросу."

        return {
            "answer": answer,
            "tool_trace": tool_trace,
            "retrieved_chunk_ids": _chunk_ids(accumulated),
            "retrieved_chunks": accumulated,
            "route_trace": state.route_trace + [
                f"search_knowledge: max iterations reached, {len(accumulated)} chunks used (fallback)"
            ],
        }

    except Exception as e:
        print(f"[search_knowledge] Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "answer": f"Ошибка RAG-агента: {e}",
            "tool_trace": tool_trace,
            "retrieved_chunk_ids": _chunk_ids(accumulated),
            "retrieved_chunks": accumulated,
            "errors": state.errors + [f"search_knowledge error: {e}"],
            "route_trace": state.route_trace + ["search_knowledge: exception"],
        }