import os
import sys
import logging
from typing import List, Optional

from fastmcp import FastMCP

# Ensure we can import from project src when running this file directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from database import GroupDatabase  # noqa: E402
from database import db_config  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
try:
    group_db = GroupDatabase(db_config.url)
    logger.info("Database service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise

mcp_server = FastMCP(name="DatabaseService")


@mcp_server.tool
async def create_group(
    name: str, user_ids: Optional[List[int]] = None, description: Optional[str] = None
) -> str:
    """Create a new group with optional users and description.

    Parameters:
    - name: Name of the group (required)
    - user_ids: List of Telegram user IDs to add to the group (optional)
    - description: Description of the group (optional)
    """
    try:
        group = group_db.create_group(
            name=name, user_ids=user_ids, description=description
        )
        result = f"Group '{name}' created successfully with ID: {group['id']}"
        if user_ids:
            result += f"\nAdded {len(user_ids)} users to the group"
        return result
    except ValueError as e:
        return f"Error creating group: {str(e)}"
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        return f"Database error: {str(e)}"


@mcp_server.tool
async def delete_group(group_id: int) -> str:
    """Delete a group by its ID.

    Parameters:
    - group_id: ID of the group to delete
    """
    try:
        success = group_db.delete_group(group_id)
        if success:
            return f"Group with ID {group_id} deleted successfully"
        else:
            return f"Group with ID {group_id} not found"
    except Exception as e:
        logger.error(f"Error deleting group: {e}")
        return f"Database error: {str(e)}"


@mcp_server.tool
async def add_user_to_group(group_id: int, telegram_id: int) -> str:
    """Add a user to a group.

    Parameters:
    - group_id: ID of the group
    - telegram_id: Telegram ID of the user to add
    """
    try:
        success = group_db.add_user_to_group(group_id, telegram_id)
        if success:
            return f"User {telegram_id} added to group {group_id} successfully"
        else:
            return f"Failed to add user {telegram_id} to group {group_id}. Check if both exist."
    except Exception as e:
        logger.error(f"Error adding user to group: {e}")
        return f"Database error: {str(e)}"


@mcp_server.tool
async def remove_user_from_group(group_id: int, telegram_id: int) -> str:
    """Remove a user from a group.

    Parameters:
    - group_id: ID of the group
    - telegram_id: Telegram ID of the user to remove
    """
    try:
        success = group_db.remove_user_from_group(group_id, telegram_id)
        if success:
            return f"User {telegram_id} removed from group {group_id} successfully"
        else:
            return f"Failed to remove user {telegram_id} from group {group_id}. Check if both exist and user is in the group."
    except Exception as e:
        logger.error(f"Error removing user from group: {e}")
        return f"Database error: {str(e)}"


@mcp_server.tool
async def create_user(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> str:
    """Create a new user in the database.

    Parameters:
    - telegram_id: User's Telegram ID (required)
    - username: Telegram username (optional)
    - first_name: User's first name (optional)
    - last_name: User's last name (optional)
    """
    try:
        user = group_db.create_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        return f"User created successfully with ID: {user.id}, Telegram ID: {user.telegram_id}"
    except ValueError as e:
        return f"Error creating user: {str(e)}"
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return f"Database error: {str(e)}"


@mcp_server.tool
async def get_all_groups() -> str:
    """Get a list of all groups in the database."""
    try:
        groups = group_db.get_all_groups()
        if not groups:
            return "No groups found in the database"

        result = "Groups in the database:\n"
        for group in groups:
            result += f"- ID: {group['id']}, Name: '{group['name']}'"
            if group["description"]:
                result += f", Description: '{group['description']}'"
            result += f", Users: {group['users_count']}\n"

        return result
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return f"Database error: {str(e)}"


@mcp_server.tool
async def get_group_by_id(group_id: int) -> str:
    """Get detailed information about a specific group.

    Parameters:
    - group_id: ID of the group to retrieve
    """
    try:
        group = group_db.get_group_by_id(group_id)
        if not group:
            return f"Group with ID {group_id} not found"

        result = "Group Details:\n"
        result += f"- ID: {group['id']}\n"
        result += f"- Name: '{group['name']}'\n"
        if group['description']:
            result += f"- Description: '{group['description']}'\n"
        result += f"- Created: {group['created_at']}\n"
        result += f"- Users ({group['users_count']}):\n"

        for user in group['users']:
            result += f"  * {user['telegram_id']}"
            if user['username']:
                result += f" (@{user['username']})"
            if user['first_name'] or user['last_name']:
                result += f" - {user['first_name'] or ''} {user['last_name'] or ''}".strip()
            result += "\n"

        return result
    except Exception as e:
        logger.error(f"Error getting group: {e}")
        return f"Database error: {str(e)}"


@mcp_server.tool
async def get_group_by_name(name: str) -> str:
    """Get detailed information about a group by its name.

    Parameters:
    - name: Name of the group to retrieve
    """
    try:
        group = group_db.get_group_by_name(name)
        if not group:
            return f"Group with name '{name}' not found"

        result = "Group Details:\n"
        result += f"- ID: {group['id']}\n"
        result += f"- Name: '{group['name']}'\n"
        if group["description"]:
            result += f"- Description: '{group['description']}'\n"
        result += f"- Created: {group['created_at']}\n"
        result += f"- Users ({group['users_count']}):\n"

        for user in group["users"]:
            result += f"  * {user['telegram_id']}"
            if user["username"]:
                result += f" (@{user['username']})"
            if user["first_name"] or user["last_name"]:
                result += (
                    f" - {user['first_name'] or ''} {user['last_name'] or ''}".strip()
                )
            result += "\n"

        return result
    except Exception as e:
        logger.error(f"Error getting group: {e}")
        return f"Database error: {str(e)}"


@mcp_server.tool
async def get_all_users() -> str:
    """Get a list of all users in the database."""
    try:
        users = group_db.get_all_users()
        if not users:
            return "No users found in the database"

        result = "Users in the database:\n"
        for user in users:
            result += f"- ID: {user['id']}, Telegram ID: {user['telegram_id']}"
            if user["username"]:
                result += f", Username: @{user['username']}"
            if user["first_name"] or user["last_name"]:
                result += f", Name: {user['first_name'] or ''} {user['last_name'] or ''}".strip()
            result += f", Groups: {user['groups_count']}\n"

        return result
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return f"Database error: {str(e)}"


@mcp_server.tool
async def get_user_by_telegram_id(telegram_id: int) -> str:
    """Get detailed information about a user by their Telegram ID.

    Parameters:
    - telegram_id: Telegram ID of the user to retrieve
    """
    try:
        user = group_db.get_user_by_telegram_id(telegram_id)
        if not user:
            return f"User with Telegram ID {telegram_id} not found"

        result = "User Details:\n"
        result += f"- ID: {user['id']}\n"
        result += f"- Telegram ID: {user['telegram_id']}\n"
        if user["username"]:
            result += f"- Username: @{user['username']}\n"
        if user["first_name"]:
            result += f"- First Name: {user['first_name']}\n"
        if user["last_name"]:
            result += f"- Last Name: {user['last_name']}\n"
        result += f"- Created: {user['created_at']}\n"
        result += f"- Groups ({user['groups_count']}):\n"

        for group in user["groups"]:
            result += f"  * {group['name']} (ID: {group['id']})\n"

        return result
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return f"Database error: {str(e)}"


def main() -> None:
    """Run the MCP server."""
    # Get configuration from environment variables
    host = os.getenv("DATABASE_SERVICE_MCP_HOST", "0.0.0.0")
    port = int(os.getenv("DATABASE_SERVICE_MCP_PORT", "8092"))

    logger.info(f"Starting Database Service MCP server on {host}:{port}")

    mcp_server.run(
        transport="http",
        host=host,
        port=port,
    )


if __name__ == "__main__":
    main()
