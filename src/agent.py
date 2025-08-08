import os

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_openai import ChatOpenAI


async def build_agent():
    """
    Builds an OpenAI-based agent using the LangChain framework,
    integrated with a simple FastMCP server for local development.

    The agent does not persist conversation history in memory.
    """
    
    llm = ChatOpenAI(
        temperature=1,
        streaming=False,
        model=os.environ.get("OPENAI_MODEL", "gpt-5-nano"),
        api_key=os.environ.get("OPENAI_API_KEY", None)
    )

    try:
        # Create client to connect to our MCP server
        client = MultiServerMCPClient({
            "SimpleMCPServer": {
                "transport": "streamable_http",
                "url": "http://localhost:8080/mcp/"
            }
        })
        tools = await client.get_tools()
        print(f"✅ Connected to MCP server at http://localhost:8080/mcp/")
            
    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {e}")
        # Return empty tools if MCP server is not available
        tools = []

    def call_model(state: MessagesState):
        try:
            if tools:
                response = llm.bind_tools(tools).invoke(state["messages"])
            else:
                response = llm.invoke(state["messages"])
            return {"messages": response}
        except Exception as e:
            print(f"Error in call_model: {e}")
            # Return a simple error message
            from langchain_core.messages import AIMessage
            return {"messages": [AIMessage(content="Sorry, I encountered an error processing your request.")]}

    builder = StateGraph(MessagesState)
    builder.add_node(call_model)
    if tools:
        builder.add_node(ToolNode(tools))
        builder.add_edge(START, "call_model")
        builder.add_conditional_edges(
            "call_model",
            tools_condition,
        )
        builder.add_edge("tools", "call_model")
    else:
        builder.add_edge(START, "call_model")

    return builder.compile()