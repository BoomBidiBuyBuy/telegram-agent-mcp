import os
import logging
import asyncio
import json

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver

from langchain_openai import ChatOpenAI
from envs import MCP_SERVER_URL, MCP_SERVER_TRANSPORT, MCP_SERVERS_FILE_PATH


logger = logging.getLogger(__name__)

# Global agent instance
agent = None
agent_initializing = False


async def build_agent():
    """
    Builds an OpenAI-based agent using the LangChain framework,
    integrated with a simple FastMCP server for local development.

    The agent uses InMemorySaver to persist conversation history.
    """
    llm = ChatOpenAI(
        temperature=1,
        streaming=False,
        model=os.environ.get("OPENAI_MODEL", "gpt-5-nano"),
        api_key=os.environ.get("OPENAI_API_KEY", None),
    )

    try:
        # Create client to connect to our MCP server

        logger.info(
            "Connecting to MCP server: %s with transport: %s",
            MCP_SERVER_URL,
            MCP_SERVER_TRANSPORT,
        )

        mcp_servers = load_mcp_servers()

        client = MultiServerMCPClient(mcp_servers)
        tools = await client.get_tools()
        logger.info("Connected to MCP server at %s", MCP_SERVER_URL)
        logger.info("Loaded %d tools: %s", len(tools), [tool.name for tool in tools])

    except Exception as e:
        logger.exception("Failed to connect to MCP server: %s", e)
        # Return empty tools if MCP server is not available
        tools = []

    def call_model(state: MessagesState):
        try:
            logger.info("Processing message with LLM...")
            logger.debug("State messages: %s", state["messages"])

            if tools:
                logger.info(
                    "Using %d tools: %s", len(tools), [tool.name for tool in tools]
                )
                response = llm.bind_tools(tools).invoke(state["messages"])
                logger.debug("LLM response with tools: %s", response)
            else:
                logger.info("Using LLM without tools")
                response = llm.invoke(state["messages"])
                logger.debug("LLM response without tools: %s", response)
            return {"messages": response}
        except Exception as e:
            logger.exception("Error in call_model: %s", e)
            # Return a simple error message
            from langchain_core.messages import AIMessage

            return {
                "messages": [
                    AIMessage(
                        content="Sorry, I encountered an error processing your request."
                    )
                ]
            }

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

    # Use InMemorySaver to persist conversation history
    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)


async def get_agent():
    """Get or initialize the agent (lazy initialization)"""
    global agent, agent_initializing

    if agent is not None:
        return agent

    if agent_initializing:
        # Wait for initialization to complete
        while agent_initializing:
            await asyncio.sleep(0.1)
        return agent

    agent_initializing = True
    try:
        logger.info("Initializing agent...")
        agent = await build_agent()
        logger.info("Agent initialized successfully")
        return agent
    finally:
        agent_initializing = False


def _expand_env_vars(value):
    """Recursively expand ${VAR} or $VAR in strings inside dict/list structures."""
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, dict):
        return {k: _expand_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env_vars(v) for v in value]
    return value


def load_mcp_servers():
    with open(MCP_SERVERS_FILE_PATH) as f:
        permanent_servers = json.load(f)
    mcp_servers = permanent_servers.get("mcpServers", {})
    mcp_servers = _expand_env_vars(mcp_servers)
    logger.info("Loaded MCP servers: %s", mcp_servers)
    return mcp_servers
