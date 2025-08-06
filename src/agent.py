import asyncio
import os

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, MessagesState, START
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_openai import ChatOpenAI
from mcp_tools import ensure_mcp_server


async def build_agent():
    """
    Builds an OpenAI-based agent using the LangChain framework,
    integrated with a simple FastMCP server for local development.

    The agent does not persist conversation history in memory.
    """
    # Ensure MCP server is running
    ensure_mcp_server()
    
    llm = ChatOpenAI(
        temperature=0,
        streaming=False,
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.environ.get("OPENAI_API_KEY", None)
    )

    # Create client to connect to our MCP server
    client = MultiServerMCPClient({
        "SimpleMCPServer": {
            "transport": "sse",
            "url": "http://localhost:8080/sse"
        }
    })

    # get tools
    tools = await client.get_tools()

    def call_model(state: MessagesState):
        response = llm.bind_tools(tools).invoke(state["messages"])
        return {"messages": response}

    builder = StateGraph(MessagesState)
    builder.add_node(call_model)
    builder.add_node(ToolNode(tools))
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges(
        "call_model",
        tools_condition,
    )
    builder.add_edge("tools", "call_model")

    return builder.compile()