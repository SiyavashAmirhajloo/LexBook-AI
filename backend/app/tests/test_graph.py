"""Graph routing check (V4): chat → rag, study → study."""
import asyncio

from app.agents.graph import build_graph, run_graph


def test_graph_has_all_agent_nodes():
    nodes = set(build_graph().nodes.keys())
    assert {"coordinator", "planner", "rag", "study", "memory", "evaluation"} <= nodes


def test_chat_intent_routes_to_rag():
    state = asyncio.run(run_graph(text="What is the passive voice?", intent="chat"))
    assert state["route"] == "rag"
    assert any("rag_agent" in line for line in state["trace"])


def test_study_intent_routes_to_study():
    state = asyncio.run(run_graph(text="I finished Unit 7", intent="study"))
    assert state["route"] == "study"
    assert any("study_agent" in line for line in state["trace"])
