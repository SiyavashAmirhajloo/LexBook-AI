"""Graph routing checks (V4/V5): chat → rag, study → study, internet → internet."""
import asyncio

from app.agents.graph import build_graph, run_graph


def test_graph_has_all_agent_nodes():
    nodes = set(build_graph().nodes.keys())
    assert {
        "coordinator",
        "planner",
        "rag",
        "study",
        "internet",
        "memory",
        "evaluation",
    } <= nodes


def test_chat_intent_routes_to_rag():
    state = asyncio.run(run_graph(text="What is the passive voice?", intent="chat"))
    assert state["route"] == "rag"
    assert any("rag_agent" in line for line in state["trace"])


def test_study_intent_routes_to_study():
    state = asyncio.run(run_graph(text="I finished Unit 7", intent="study"))
    assert state["route"] == "study"
    assert any("study_agent" in line for line in state["trace"])


def test_internet_intent_routes_to_internet():
    state = asyncio.run(
        run_graph(text="find resources", intent="internet", topics=["Passive Voice"])
    )
    assert state["route"] == "internet"
    assert any("internet_agent" in line for line in state["trace"])
