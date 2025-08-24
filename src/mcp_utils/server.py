import logging

from envs import MCP_HOST, MCP_PORT
from fastmcp import FastMCP
from starlette.responses import JSONResponse

from mcp_utils.manage_user_groups import (
    create_group,
    delete_group,
    add_user_to_group,
    remove_user_from_group,
    create_user,
    get_all_groups,
    get_group_by_id,
    get_group_by_name,
    get_all_users,
    get_user_by_telegram_id,
)
from mcp_utils.telegram_utils import send_message_to_user

logger = logging.getLogger(__name__)


mcp_server = FastMCP(name="telegram-agent-mcp")


@mcp_server.custom_route("/health", methods=["GET"])
async def http_health_check(request):
    return JSONResponse({"status": "healthy", "service": "telegram-agent-mcp"})


def run_mcp_app() -> None:
    """Run the MCP server."""

    for tool in [
        create_group,
        delete_group,
        add_user_to_group,
        remove_user_from_group,
        create_user,
        get_all_groups,
        get_group_by_id,
        get_group_by_name,
        get_all_users,
        get_user_by_telegram_id,
        send_message_to_user,
    ]:
        mcp_server.tool(tool)

    mcp_server.run(
        transport="http",
        host=MCP_HOST,
        port=MCP_PORT,
    )
