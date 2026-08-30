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
    if intent in ("study", "internet", "personalize", "plan"):
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


async def study_planner_agent(state: dict) -> dict:
    """Study Planner Agent (V10 flagship): decides what to study next.

    The deterministic reasoning runs in services/planner.py (this node
    stays a thin orchestrator like the other agents). Expects state to
    carry `plan_result` computed by the API layer.
    """
    plan = state.get("plan_result") or {}
    skill = plan.get("focus_skill", "?")
    topic = plan.get("recommended_topic", "?")
    reasons = len(plan.get("reasoning", []))
    state["trace"].append(
        f"study_planner: skill={skill!r} topic={topic!r} reasoning_steps={reasons}"
    )
    state["evaluations"].append(
        {
            "agent": "study_planner",
            # Grounded = the plan has at least one data-driven reason.
            "grounded": reasons > 0,
            "sources": len(plan.get("weak_topics", [])) + len(plan.get("due_reviews", [])),
        }
    )
    return state


async def memory_agent(state: dict) -> dict:
    """Memory Agent: real long-term memory read+write (V7).

    Reads a memory snapshot from the DB (if one was provided in state by the
    API layer) and writes back any new facts / vocabulary the LLM extracted
    from the user's current message. The agent stays a thin orchestrator —
    the heavy work lives in services/memory.py so this can be unit-tested
    with an in-memory database later.
    """
    db = state.get("db")
    snapshot = state.get("memory_snapshot") or {}
    trace = state.get("trace", [])

    if db is not None:
        from app.services.memory import add_fact, extract_memories, learn_word

        # WRITE: extract facts + vocabulary from the current text and persist.
        text = state.get("text", "")
        extracted = await extract_memories(text)
        for f in extracted.get("facts", []):
            await add_fact(
                db, f.get("text", ""), category=f.get("category", "fact"), source="chat"
            )
        for v in extracted.get("vocabulary", []):
            await learn_word(
                db, v.get("word", ""), topic=v.get("topic", "general")
            )

        # READ: refresh the snapshot so downstream agents/UI see the latest.
        from app.services.memory import memory_snapshot as _snapshot
        snapshot = await _snapshot(db)
        state["memory_snapshot"] = snapshot

    facts_n = len(snapshot.get("facts", []))
    vocab_n = len(snapshot.get("vocabulary", []))
    weak_n = len(snapshot.get("weak_topics", []))
    trace.append(
        f"memory_agent: facts={facts_n} vocab={vocab_n} weak_topics={weak_n}"
    )
    state["trace"] = trace
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
