import sqlite3
import json
from typing import Annotated
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode, tools_condition
from dotenv import load_dotenv
from setup import llm
from Tools import render_mermaid

load_dotenv()

app = FastAPI(title="CodeAtlas API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── LangGraph Setup ────────────────────────────────────────────────────────

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

conn = sqlite3.connect(database="Chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

conn.execute("""
    CREATE TABLE IF NOT EXISTS thread_names (
        thread_id TEXT PRIMARY KEY,
        name TEXT NOT NULL
    )
""")
conn.commit()

tools = [render_mermaid]
llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools)

SYSTEM_PROMPT = """You are CodeAtlas, an AI assistant that analyses source code and generates architecture diagrams in Mermaid format.

Your workflow:
1. When a user shares code (ABAP or any language) or describes a feature/module, analyse it to identify:
   - Actors and users
   - Processes and business logic
   - Data structures and how data is stored
   - Integrations and data flows between components

2. Build the diagram incrementally through conversation:
   - Ask clarifying questions if the scope is unclear
   - Show your Mermaid code as a draft inside a ```mermaid code block so the user can review it
   - Refine based on user feedback — add, remove, or restructure elements as requested
   - You can suggest the most appropriate diagram type (flowchart, sequence, ER, class, etc.) based on what the user is trying to show

3. Only call the render_mermaid tool to generate the actual image when the user explicitly confirms — for example when they say "generate it", "looks good", "create the diagram", or "yes go ahead". Never render without that confirmation.

4. If the user pastes existing Mermaid code at the start, treat it as the base to build on rather than starting from scratch.

Always be collaborative — your goal is to help the user arrive at an accurate, clear diagram that truly reflects the code or system being described.
"""

def chat_node(state: ChatState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    return {"messages": [llm_with_tools.invoke(messages)]}

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", END)
graph.add_edge("chat_node", END)
chatbot = graph.compile(checkpointer=checkpointer)

# ─── Thread Helpers ─────────────────────────────────────────────────────────

def _get_thread_name(thread_id: str) -> str:
    row = conn.execute(
        "SELECT name FROM thread_names WHERE thread_id = ?", (thread_id,)
    ).fetchone()
    return row[0] if row else thread_id[:8] + "..."

def _set_thread_name(thread_id: str, name: str):
    conn.execute(
        "INSERT INTO thread_names (thread_id, name) VALUES (?, ?) "
        "ON CONFLICT(thread_id) DO UPDATE SET name = excluded.name",
        (thread_id, name)
    )
    conn.commit()

# ─── Request / Response Models ───────────────────────────────────────────────

class ChatRequest(BaseModel):
    thread_id: str
    message: str

class RenameRequest(BaseModel):
    name: str

# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/threads")
def list_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return [
        {"thread_id": t, "name": _get_thread_name(t)}
        for t in all_threads
    ]

@app.get("/threads/{thread_id}/history")
def get_history(thread_id: str):
    state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
    messages = state.values.get("messages", [])
    result = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            result.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage) and msg.content:
            result.append({"role": "ai", "content": msg.content})
    return result

@app.put("/threads/{thread_id}/name")
def rename_thread(thread_id: str, body: RenameRequest):
    _set_thread_name(thread_id, body.name)
    return {"status": "ok"}

@app.delete("/threads/{thread_id}")
def delete_thread(thread_id: str):
    for table in ("checkpoints", "checkpoint_blobs", "checkpoint_writes"):
        conn.execute(f"DELETE FROM {table} WHERE thread_id = ?", (thread_id,))
    conn.execute("DELETE FROM thread_names WHERE thread_id = ?", (thread_id,))
    conn.commit()
    return {"status": "ok"}

@app.post("/chat")
def chat(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}

    def event_stream():
        for message_chunk, _ in chatbot.stream(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
            stream_mode="messages"
        ):
            if isinstance(message_chunk, ToolMessage):
                payload = json.dumps({
                    "type": "tool",
                    "name": getattr(message_chunk, "name", "tool"),
                    "content": message_chunk.content,
                })
                yield f"data: {payload}\n\n"
            elif isinstance(message_chunk, AIMessage) and message_chunk.content:
                payload = json.dumps({
                    "type": "token",
                    "content": message_chunk.content,
                })
                yield f"data: {payload}\n\n"
        yield 'data: {"type": "done"}\n\n'

    return StreamingResponse(event_stream(), media_type="text/event-stream")
