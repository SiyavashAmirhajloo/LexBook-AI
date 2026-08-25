"""LangGraph workflow definition (V4, extended in V5).

Builds the multi-agent graph:
    coordinator → planner → conditional → agent → memory → evaluation

Routes on the planner's primary plan:
    "rag"      → RAG Agent
    "study"    → Study Agent
    "internet" → Internet Agent (V5)
    else       → RAG Agent (fallback)
"""
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    coordinator_node,
    evaluation_agent,
    internet_agent,
    memory_agent,
    personalize_agent,
    planner_node,
    rag_agent,
    study_agent,
)

_AGENT_ROUTES = ("study", "internet", "personalize", "rag")


def _route_to_agent(state: dict) -> Literal["study", "internet", "personalize", "rag"]:
    plan = state.get("plan") or [state.get("intent", "rag")]
    primary = plan[0] if isinstance(plan, list) and plan else "rag"
    return primary if primary in _AGENT_ROUTES else "rag"


def build_graph() -> Any:
    """Build the coordinator→planner→agent→memory→evaluation graph."""
    g = StateGraph(dict)

    g.add_node("coordinator", coordinator_node)
    g.add_node("planner", planner_node)
    g.add_node("rag", rag_agent)
    g.add_node("study", study_agent)
    g.add_node("internet", internet_agent)
    g.add_node("personalize", personalize_agent)
    g.add_node("memory", memory_agent)
    g.add_node("evaluation", evaluation_agent)

    g.add_edge(START, "coordinator")
    g.add_edge("coordinator", "planner")
    g.add_conditional_edges(
        "planner",
        _route_to_agent,
        {"study": "study", "internet": "internet", "personalize": "personalize", "rag": "rag"},
    )
    g.add_edge("rag", "memory")
    g.add_edge("study", "memory")
    g.add_edge("internet", "memory")
    g.add_edge("personalize", "memory")
    g.add_edge("memory", "evaluation")
    g.add_edge("evaluation", END)

    return g.compile()


async def run_graph(
    text: str,
    intent: str = "chat",
    context_block: str = "",
    citations: list[dict] | None = None,
    study_result: dict | None = None,
    facts: list[dict] | None = None,
    new_facts: list[dict] | None = None,
    topics: list[str] | None = None,
    resources: list[dict] | None = None,
    personalization: dict | None = None,
) -> dict:
    """Invoke the graph with the given request and return the final state.

    This is the entry point used by the API layer. Heavy work (retrieval,
    extraction, web search) stays in the service layer; the graph orchestrates,
    routes, and evaluates.
    """
    initial = {
        "text": text,
        "intent": intent,
        "context_block": context_block,
        "citations": citations or [],
        "study_result": study_result,
        "topics": topics or [],
        "resources": resources or [],
        "personalization": personalization or {},
        "facts": facts or [],
        "new_facts": new_facts or [],
        "recalled_facts": [],
        "trace": [],
        "evaluations": [],
        "plan": None,
        "route": None,
    }
    graph = build_graph()
    return await graph.ainvoke(initial)
