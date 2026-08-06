from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
#from langchain_openai import ChatOpenAI
#from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode, tools_condition
from setup import llm
from Tools import render_mermaid

load_dotenv()

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state:ChatState):
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

conn = sqlite3.connect(database='Chatbot.db',check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

tools = [render_mermaid]

llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools)

graph = StateGraph(ChatState)

graph.add_node('chat_node',chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START,'chat_node')
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge('tools',END)
graph.add_edge('chat_node',END)

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)

