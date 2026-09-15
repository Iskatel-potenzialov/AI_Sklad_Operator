"""
LangGraph: определение графа workflow склада канцелярии.

Граф:

START
  ↓
parse_request (LLM-классификация)
  ↓
route_request (Python-маршрутизация)
  ├─→ answer_general → END                           (general_question)
  ├─→ search_knowledge → END                         (search_knowledge)
  └─→ load_items
        ↓
      route_after_load
        ├─→ find_problem_items → analyze_items → END   (inventory_analysis)
        ├─→ load_supplier_files → check_order_conditions
        │       ↓
        │     route_after_check
        │       ├─→ END                                 (check_order_conditions)
        │       └─→ confirm_order → END                 (confirm_order)
        └─→ prepare_update → execute_update → END       (update_min_stock)
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.graph.state import GraphState
from backend.graph.nodes.parse_request import parse_request
from backend.graph.nodes.route_request import route_request
from backend.graph.nodes.answer_general import answer_general
from backend.graph.nodes.load_items import load_items
from backend.graph.nodes.find_problem_items import find_problem_items
from backend.graph.nodes.analyze_items import analyze_items
from backend.graph.nodes.load_supplier_files import load_supplier_files
from backend.graph.nodes.check_order_conditions import check_order_conditions
from backend.graph.nodes.confirm_order import confirm_order
from backend.graph.nodes.route_after_load import route_after_load
from backend.graph.nodes.route_after_check import route_after_check
from backend.graph.nodes.prepare_update import prepare_update
from backend.graph.nodes.execute_update import execute_update
from backend.graph.nodes.search_knowledge import search_knowledge


def build_graph():
    """
    Строит и компилирует LangGraph граф.
    """
    graph = StateGraph(GraphState)

    # --- Узлы ---
    graph.add_node("parse_request", parse_request)
    graph.add_node("answer_general", answer_general)
    graph.add_node("search_knowledge", search_knowledge)
    graph.add_node("load_items", load_items)
    graph.add_node("find_problem_items", find_problem_items)
    graph.add_node("analyze_items", analyze_items)
    graph.add_node("load_supplier_files", load_supplier_files)
    graph.add_node("check_order_conditions", check_order_conditions)
    graph.add_node("confirm_order", confirm_order)
    graph.add_node("prepare_update", prepare_update)
    graph.add_node("execute_update", execute_update)

    # --- START → parse_request ---
    graph.add_edge(START, "parse_request")

    # --- После parse_request ---
    # route_request возвращает: answer_general | search_knowledge | load_items
    graph.add_conditional_edges(
        "parse_request",
        route_request,
        {
            "answer_general": "answer_general",
            "search_knowledge": "search_knowledge",
            "load_items": "load_items",
        }
    )

    # Ветка общих вопросов
    graph.add_edge("answer_general", END)

    # Ветка RAG-поиска по базе знаний
    graph.add_edge("search_knowledge", END)

    # --- После load_items ---
    # route_after_load возвращает: find_problem_items | load_supplier_files | prepare_update
    graph.add_conditional_edges(
        "load_items",
        route_after_load,
        {
            "find_problem_items": "find_problem_items",
            "load_supplier_files": "load_supplier_files",
            "prepare_update": "prepare_update",
        }
    )

    # Ветка анализа склада
    graph.add_edge("find_problem_items", "analyze_items")
    graph.add_edge("analyze_items", END)

    # Ветка работы с поставщиком
    graph.add_edge("load_supplier_files", "check_order_conditions")

    # --- После check_order_conditions ---
    # route_after_check возвращает: end | confirm_order
    graph.add_conditional_edges(
        "check_order_conditions",
        route_after_check,
        {
            "end": END,
            "confirm_order": "confirm_order",
        }
    )

    # confirm_order → END
    graph.add_edge("confirm_order", END)

    # --- Ветка обновления min_stock ---
    graph.add_edge("prepare_update", "execute_update")
    graph.add_edge("execute_update", END)

    # --- Компиляция ---
    # MemorySaver нужен для HITL: interrupt() сохраняет состояние,
    # чтобы потом возобновить его через Command(resume=...)
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# Компилированный граф (singleton)
compiled_graph = build_graph()