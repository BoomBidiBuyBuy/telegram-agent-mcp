import logging
from typing import Annotated, List, Optional

from user_group_db.models import Group, User
from storage import SessionLocal

logger = logging.getLogger(__name__)



async def create_group(
    name: Annotated[str, "Name of the group"],
    user_ids: Annotated[Optional[List[int]], "List of Telegram user IDs to add to the group"] = None,
    description: Annotated[Optional[str], "Description of the group"] = None
) -> str:
    """Create a new group with optional users and description."""
    logger.info(f"Creating group: {name}, user_ids: {user_ids}, description: {description}")

    try:    
        with SessionLocal() as session:
            group = Group.create(
                name=name, user_ids=user_ids, description=description, session=session
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


async def delete_group(group_id: Annotated[int, "ID of the group to delete"]) -> str:
    """Delete a group by its ID."""
    logger.info(f"Deleting group: {group_id}")
    try:
        with SessionLocal() as session:
            success = Group.delete_by_id(group_id, session)
        if success:
            return f"Group with ID {group_id} deleted successfully"
        else:
            return f"Group with ID {group_id} not found"
    except Exception as e:
        logger.error(f"Error deleting group: {e}")
        return f"Database error: {str(e)}"


async def add_user_to_group(group_id: Annotated[int, "ID of the group"], telegram_id: Annotated[int, "Telegram ID of the user to add"]) -> str:
    """Add a user to a group."""
    logger.info(f"Adding user {telegram_id} to group {group_id}")
    try:
        with SessionLocal() as session:
            success = Group.add_user(group_id, telegram_id, session)
        if success:
            return f"User {telegram_id} added to group {group_id} successfully"
        else:
            return f"Failed to add user {telegram_id} to group {group_id}. Check if both exist."
    except Exception as e:
        logger.error(f"Error adding user to group: {e}")
        return f"Database error: {str(e)}"


async def remove_user_from_group(group_id: Annotated[int, "ID of the group"], telegram_id: Annotated[int, "Telegram ID of the user to remove"]) -> str:
    """Remove a user from a group."""
    logger.info(f"Removing user {telegram_id} from group {group_id}")
    try:
        with SessionLocal() as session:
            success = Group.remove_user(group_id, telegram_id, session)
        if success:
            return f"User {telegram_id} removed from group {group_id} successfully"
        else:
            return f"Failed to remove user {telegram_id} from group {group_id}. Check if both exist and user is in the group."
    except Exception as e:
        logger.error(f"Error removing user from group: {e}")
        return f"Database error: {str(e)}"


async def create_user(
    telegram_id: Annotated[int, "Telegram ID of the user to create"],
    username: Annotated[Optional[str], "Telegram username of the user to create"] = None,
    first_name: Annotated[Optional[str], "First name of the user to create"] = None,
    last_name: Annotated[Optional[str], "Last name of the user to create"] = None,
) -> str:
    """Create a new user in the database."""
    logger.info(f"Creating user: {telegram_id}, username: {username}, first_name: {first_name}, last_name: {last_name}")
    try:
        with SessionLocal() as session:
            user = User.create(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            session=session
        )
        return f"User created successfully with ID: {user.id}, Telegram ID: {user.telegram_id}"
    except ValueError as e:
        return f"Error creating user: {str(e)}"
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return f"Database error: {str(e)}"


async def get_all_groups() -> str:
    """Get a list of all groups in the database."""
    logger.info("Getting all groups")
    try:
        with SessionLocal() as session:
            groups = Group.get_all(session)
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


async def get_group_by_id(group_id: Annotated[int, "ID of the group to retrieve"]) -> str:
    """Get detailed information about a specific group."""
    logger.info(f"Getting group by ID: {group_id}")
    try:
        with SessionLocal() as session:
            group = Group.get_by_id(group_id, session)
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


async def get_group_by_name(name: Annotated[str, "Name of the group to retrieve"]) -> str:
    """Get detailed information about a group by its name."""
    logger.info(f"Getting group by name: {name}")
    try:
        with SessionLocal() as session:
            group = Group.get_by_name(name, session)
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


async def get_all_users() -> str:
    """Get a list of all users in the database."""
    logger.info("Getting all users")
    try:    
        with SessionLocal() as session:
            users = User.get_all(session)
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


async def get_user_by_telegram_id(telegram_id: Annotated[int, "Telegram ID of the user to retrieve"]) -> str:
    """Get detailed information about a user by their Telegram ID."""
    logger.info(f"Getting user by Telegram ID: {telegram_id}")
    try:
        with SessionLocal() as session:
            user = User.get_by_telegram_id(telegram_id, session)
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
