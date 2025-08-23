import logging
import envs
from fastmcp import FastMCP

from mcp.manage_user_groups import create_group, delete_group, add_user_to_group, remove_user_from_group, create_user, get_all_groups, get_group_by_id, get_group_by_name, get_all_users, get_user_by_telegram_id
from mcp.telegram import send_message_to_user

logger = logging.getLogger(__name__)


mcp_server = FastMCP(name="telegram-agent-mcp")


def main() -> None:
    """Run the MCP server."""

    for tool in [
        create_group, delete_group, add_user_to_group,
        remove_user_from_group, create_user, get_all_groups,
        get_group_by_id, get_group_by_name, get_all_users,
        get_user_by_telegram_id, send_message_to_user]:
        mcp_server.tool(tool)

    mcp_server.run(
        transport="http",
        host=envs.MCP_HOST,
        port=envs.MCP_PORT,
    )


if __name__ == "__main__":
    main()
