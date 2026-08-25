"""Agent nodes for the LangGraph workflow (V4).

Each agent is a plain async function operating on the shared graph state.
Nodes are pure routing/work units; DB access is passed in through the state.
"""


async def coordinator_node(state: dict) -> dict:
    """Entry point: all requests funnel through here, then go to the planner.

    The planner owns route selection (it runs next and is what the conditional
    edge reads), so the coordinator only records the incoming intent.
    """
    intent = state.get("intent", "chat")
    state["trace"].append(f"coordinator: intent={intent!r} -> planner")
    return state


def _plan_chat(text: str) -> list[str]:
    """Default planner for chat requests: RAG always, study for queries that
    describe what was just studied."""
    lower = text.lower()
    study_markers = ["finished", "completed", "studied", "read", "went through",
                     "covered", "learned", "just studied"]
    if any(m in lower for m in study_markers):
        return ["study"]
    return ["rag"]


async def planner_node(state: dict) -> dict:
    """Minimal planner: decide which agent(s) handle the request.

    An explicit intent from the API layer wins; otherwise infer from the text.
    For V4 this is keyword-based (an LLM planner can replace it later).
    """
    text = state.get("text", "")
    intent = state.get("intent", "chat")
    if intent in ("study", "internet", "personalize"):
        plan = [intent]
    else:
        plan = _plan_chat(text)
    state["plan"] = plan
    state["route"] = plan[0]
    state["trace"].append(f"planner: intent={intent!r} plan={plan} route={plan[0]!r}")
    return state


async def rag_agent(state: dict) -> dict:
    """RAG Agent: wraps the V2 retrieve-then-generate logic.

    Expects state to already carry `context_block` + `citations` (set by the
    API layer before invoking the graph). Passes them through unchanged so the
    streaming endpoint can keep its exact SSE contract.
    """
    state["trace"].append("rag_agent: passthrough (context already retrieved upstream)")
    state["evaluations"].append(
        {"agent": "rag", "grounded": True, "sources": len(state.get("citations", []))}
    )
    return state


async def study_agent(state: dict) -> dict:
    """Study Agent: wraps the V3 session/topic-extraction logic.

    Expects state to carry `study_result` (already computed by the API layer).
    """
    result = state.get("study_result")
    state["trace"].append(f"study_agent: study_result = {bool(result)}")
    if result:
        state["topic_count"] = len(result.get("topics", []))
        state["keyword_count"] = len(result.get("keywords", []))
    state["evaluations"].append({"agent": "study", "grounded": True, "sources": 1})
    return state


async def internet_agent(state: dict) -> dict:
    """Internet Agent: curates external IELTS/TOEFL resources for study topics.

    The search + LLM summarisation runs in the service layer (see
    services/resources.py) so this node stays a thin orchestration unit, the
    same pattern the RAG and Study agents use.

    Grounded is True only when every persisted resource carries a real URL —
    links are the verifiable artifact here, not generated prose.
    """
    resources = state.get("resources") or []
    topics = state.get("topics") or []
    reputable = sum(1 for r in resources if r.get("is_reputable"))
    state["trace"].append(
        f"internet_agent: topics={len(topics)} resources={len(resources)} "
        f"reputable={reputable}"
    )
    state["evaluations"].append(
        {
            "agent": "internet",
            "grounded": all(r.get("url") for r in resources),
            "sources": len(resources),
        }
    )
    return state


async def personalize_agent(state: dict) -> dict:
    """Personalization Agent: wraps V6 generation (flashcards/quiz/prompts).

    The actual LLM generation runs in services/personalization.py, driven by
    per-session endpoints. This node records the outcome for tracing and
    evaluates groundedness the same way the other agents do.
    """
    generated = state.get("personalization") or {}
    counts = {k: len(v) for k, v in generated.items() if isinstance(v, list)}
    state["trace"].append(f"personalize_agent: generated={counts or 'none'}")
    state["evaluations"].append(
        {
            "agent": "personalize",
            "grounded": True,
            "sources": sum(counts.values()),
        }
    )
    return state


async def memory_agent(state: dict) -> dict:
    """Memory Agent (stub): recalls facts that were remembered earlier.

    Full long-term memory arrives in V7; for now we round-trip a small
    per-request fact cache through the graph state.
    """
    facts = state.get("facts", [])
    recalled = state.get("recalled_facts", [])
    new_facts = state.get("new_facts", [])
    state["recalled_facts"] = recalled + new_facts
    state["facts"] = facts + new_facts
    total = len(state["facts"])
    state["trace"].append(
        f"memory_agent: new={len(new_facts)} recalled={len(recalled)} total={total}"
    )
    return state


async def evaluation_agent(state: dict) -> dict:
    """Evaluation Agent (stub): logs a groundedness estimate per request.

    Full evaluation pipeline (hallucination detection, citation accuracy,
    RAG metrics) arrives after V6. Here we emit a structured log line.
    """
    grounded = all(e.get("grounded", False) for e in state.get("evaluations", []))
    state["trace"].append(f"evaluation_agent: grounded={grounded}")
    print(f"[eval] intent={state.get('intent')} route={state.get('route')} "
          f"grounded={grounded} context_chunks={len(state.get('citations', []))}")
    return state
