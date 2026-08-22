"""LangGraph workflow definition (V4).

Builds the multi-agent graph:
    coordinator → planner → conditional → agent → memory → evaluation

Routes on the planner's primary plan:
    "rag"   → RAG Agent
    "study" → Study Agent
    else    → RAG Agent (fallback)
"""
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    coordinator_node,
    evaluation_agent,
    memory_agent,
    planner_node,
    rag_agent,
    study_agent,
)


def _route_to_agent(state: dict) -> Literal["study", "rag"]:
    plan = state.get("plan") or [state.get("intent", "rag")]
    primary = plan[0] if isinstance(plan, list) and plan else "rag"
    return "study" if primary == "study" else "rag"


def build_graph() -> Any:
    """Build the coordinator→planner→agent→memory→evaluation graph."""
    g = StateGraph(dict)

    g.add_node("coordinator", coordinator_node)
    g.add_node("planner", planner_node)
    g.add_node("rag", rag_agent)
    g.add_node("study", study_agent)
    g.add_node("memory", memory_agent)
    g.add_node("evaluation", evaluation_agent)

    g.add_edge(START, "coordinator")
    g.add_edge("coordinator", "planner")
    g.add_conditional_edges("planner", _route_to_agent, {"study": "study", "rag": "rag"})
    g.add_edge("rag", "memory")
    g.add_edge("study", "memory")
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
) -> dict:
    """Invoke the graph with the given request and return the final state.

    This is the entry point used by the API layer. It keeps the graph
    synchronous for now (LangGraph's async API can wrap these node functions);
    the heavy retrieval/extraction still happens in the service layer, then the
    graph orchestrates + routes + evaluates.
    """
    citations = citations or []
    initial = {
        "text": text,
        "intent": intent,
        "context_block": context_block,
        "citations": citations,
        "study_result": study_result,
        "facts": facts or [],
        "new_facts": new_facts or [],
        "recalled_facts": [],
        "trace": [],
        "evaluations": [],
        "plan": None,
        "route": None,
    }
    graph = build_graph()
    result = await graph.ainvoke(initial)
    return result
