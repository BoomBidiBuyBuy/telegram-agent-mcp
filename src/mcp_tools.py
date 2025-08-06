import threading
import time
from datetime import datetime
from fastmcp import FastMCP


# Global MCP server instance
mcp_server = None
mcp_thread = None


def start_mcp_server():
    """Start MCP server in a separate thread"""
    global mcp_server
    
    mcp_server = FastMCP(name="SimpleMCPServer")

    @mcp_server.tool
    def add(a: int, b: int) -> int:
        """Adds two numbers together."""
        return a + b

    @mcp_server.tool
    def current_date() -> str:
        """Returns current date and time with timezone in format %Y/%m/%d %H:%M:%S %Z%z"""
        datetime_now = datetime.now()
        return datetime_now.strftime("%Y/%m/%d %H:%M:%S %Z%z")

    @mcp_server.tool
    async def sleep(num_sec: int) -> None:
        """ Sleep num_sec seconds """
        time.sleep(num_sec)

    @mcp_server.tool
    async def kid_name() -> str:
        """ Says our kid's name """
        return "Lida"

    @mcp_server.resource("resource://config")
    def get_config() -> dict:
        """Provides the application's configuration."""
        return {
            "version": "1.0",
            "environment": "development"
        }

    # Run the server
    mcp_server.run(
        transport="sse",
        host="0.0.0.0",
        port=8080
    )


def ensure_mcp_server():
    """Ensure MCP server is running"""
    global mcp_thread
    
    if mcp_thread is None or not mcp_thread.is_alive():
        mcp_thread = threading.Thread(target=start_mcp_server, daemon=True)
        mcp_thread.start()
        # Wait a bit for server to start
        time.sleep(1) 