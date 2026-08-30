"""Chat API: streaming chat with conversation history."""
import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.agents.graph import run_graph
from app.core.db import get_db
from app.models import Conversation, Message
from app.services.chat import SYSTEM_PROMPT, build_user_prompt, retrieve_context
from app.services.llm import LLMMessage, get_llm_provider

router = APIRouter()


# ── Request / Response Schemas ─────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's question")
    conversation_id: UUID | None = Field(None, description="Existing conversation to continue")


class ConversationSummary(BaseModel):
    id: UUID
    title: str
    created_at: datetime


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    citations: list[dict]
    created_at: datetime


# ── Streaming Chat Endpoint ────────────────────────────────────────

@router.post("/chat")
async def chat_stream(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Stream an AI answer token-by-token, then emit citations as the final event.

    SSE event stream format:
    - data: {"type": "token", "content": "..."}  — emitted per token
    - data: {"type": "citations", "citations": [...]}  — final event with sources
    - data: {"type": "done"}
    """
    llm = get_llm_provider()

    # ── Retrieve context (RAG Agent) ───────────────────────────
    context_block, citations = await retrieve_context(
        db, req.message, document_id=None, top_k=6
    )

    # ── Pull a memory snapshot so the graph can write back to it ──
    from app.services.memory import memory_snapshot
    snapshot = await memory_snapshot(db)

    # ── Run the agent graph (coordinator → planner → RAG → memory → eval)
    graph_state = await run_graph(
        text=req.message,
        intent="chat",
        context_block=context_block,
        citations=citations,
        db=db,
        memory_snapshot=snapshot,
    )
    print(f"[graph] intent=chat traced={len(graph_state['trace'])} route={graph_state['route']}")
    for line in graph_state["trace"]:
        print(f"[graph]   {line}")

    # ── Build prompts (with memory context) ─────────────────────
    from app.services.memory import format_snapshot_for_prompt
    memory_block = format_snapshot_for_prompt(graph_state.get("memory_snapshot") or snapshot)
    user_prompt = build_user_prompt(req.message, context_block, memory_block=memory_block)
    messages = [LLMMessage(role="user", content=user_prompt)]

    # ── Resolve / create conversation ───────────────────────────
    conversation_id = req.conversation_id
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(title=req.message[:80])
        db.add(conversation)
        await db.flush()
        conversation_id = conversation.id

    # ── Persist user message ────────────────────────────────────
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=req.message,
        citations=[],
    )
    db.add(user_msg)
    await db.commit()

    # ── Generator: stream tokens then final citation event ──────
    async def event_stream():
        full_answer = []
        try:
            async for token in llm.stream(messages, system=SYSTEM_PROMPT):
                full_answer.append(token)
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content="".join(full_answer),
                citations=citations,
            )
            db.add(assistant_msg)
            await db.commit()

            yield f"data: {json.dumps({'type': 'citations', 'citations': citations})}\n\n"
            done_payload = json.dumps({"type": "done", "conversation_id": str(conversation_id)})
            yield f"data: {done_payload}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Conversation History APIs ──────────────────────────────────────

@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(db: AsyncSession = Depends(get_db)):
    """List all conversations, most recent first."""
    result = await db.execute(select(Conversation).order_by(Conversation.created_at.desc()))
    conversations = result.scalars().all()
    return [
        ConversationSummary(id=c.id, title=c.title, created_at=c.created_at)
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return all messages for a conversation, ordered chronologically."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()
    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            citations=m.citations or [],
            created_at=m.created_at,
        )
        for m in messages
    ]
