#!/usr/bin/env python3
"""
Database usage example for group management
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import GroupDatabase
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main function with database usage examples"""

    # Initialize database
    print("Initializing database...")
    # Use SQLite for demonstration (PostgreSQL recommended for production)
    import tempfile

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_file.close()
    database_url = f"sqlite:///{temp_file.name}"
    db = GroupDatabase(database_url)

    try:
        # Example 1: Creating users
        print("\n=== Creating users ===")

        # Create several users
        users_data = [
            {
                "telegram_id": 123456789,
                "username": "ivan_petrov",
                "first_name": "Иван",
                "last_name": "Петров",
            },
            {
                "telegram_id": 987654321,
                "username": "maria_sidorova",
                "first_name": "Мария",
                "last_name": "Сидорова",
            },
            {
                "telegram_id": 555666777,
                "username": "alex_kuznetsov",
                "first_name": "Алексей",
                "last_name": "Кузнецов",
            },
            {
                "telegram_id": 111222333,
                "username": "anna_ivanova",
                "first_name": "Анна",
                "last_name": "Иванова",
            },
        ]

        created_users = []
        for user_data in users_data:
            try:
                user = db.create_user(**user_data)
                created_users.append(user)
                print(
                    f"Created user: {user.first_name} {user.last_name} (ID: {user.telegram_id})"
                )
            except ValueError as e:
                print(f"User already exists: {e}")
                # Get existing user
                user = db.get_user_by_telegram_id(user_data["telegram_id"])
                if user:
                    created_users.append(user)

        # Example 2: Creating groups
        print("\n=== Creating groups ===")

        # Create group for beginners
        beginner_group = db.create_group(
            name="Начинающие английский",
            user_ids=[123456789, 987654321],
            description="Группа для изучения английского языка с нуля",
        )
        print(f"Created group: {beginner_group['name']} (ID: {beginner_group['id']})")

        # Create group for advanced
        advanced_group = db.create_group(
            name="Продвинутый английский",
            user_ids=[555666777],
            description="Группа для продвинутого уровня английского",
        )
        print(f"Created group: {advanced_group['name']} (ID: {advanced_group['id']})")

        # Example 3: Adding user to group
        print("\n=== Adding user to group ===")

        # Add Anna to beginners group
        success = db.add_user_to_group(beginner_group["id"], 111222333)
        if success:
            print(f"User 111222333 added to group '{beginner_group['name']}'")
        else:
            print("Failed to add user to group")

        # Example 4: Getting list of all users
        print("\n=== List of all users ===")
        all_users = db.get_all_users()
        for user in all_users:
            print(
                f"- {user.first_name} {user.last_name} (@{user.username}, ID: {user.telegram_id})"
            )

        # Example 5: Getting group information
        print("\n=== Group information ===")
        all_groups = db.get_all_groups()
        for group in all_groups:
            print(f"\nGroup: {group.name}")
            print(f"Description: {group.description}")
            # Get full group information
            group_data = db.get_group_by_id(group.id)
            if group_data:
                print(f"Number of members: {group_data['users_count']}")
                print("Members:")
                for user in group_data["users"]:
                    print(
                        f"  - {user['first_name']} {user['last_name']} (@{user['username']})"
                    )
            else:
                print("Number of members: 0")

        # Example 6: Removing user from group
        print("\n=== Removing user from group ===")

        # Remove Maria from beginners group
        success = db.remove_user_from_group(beginner_group["id"], 987654321)
        if success:
            print(f"User 987654321 removed from group '{beginner_group['name']}'")
        else:
            print("Failed to remove user from group")

        # Example 7: Searching group by name
        print("\n=== Searching group by name ===")
        found_group = db.get_group_by_name("Начинающие английский")
        if found_group:
            print(f"Found group: {found_group.name} (ID: {found_group.id})")
            # Get full group information
            group_data = db.get_group_by_id(found_group.id)
            if group_data:
                print(f"Members: {group_data['users_count']}")
            else:
                print("Members: 0")
        else:
            print("Group not found")

        # Example 8: Deleting group
        print("\n=== Deleting group ===")

        # Create temporary group for deletion demonstration
        temp_group = db.create_group(
            name="Временная группа", description="Группа для демонстрации удаления"
        )
        print(f"Created temporary group: {temp_group['name']} (ID: {temp_group['id']})")

        # Delete temporary group
        success = db.delete_group(temp_group["id"])
        if success:
            print(f"Group '{temp_group['name']}' deleted successfully")
        else:
            print("Failed to delete group")

        print("\n=== Demonstration completed ===")

    except Exception as e:
        logger.error(f"Error working with database: {e}")
        raise
    finally:
        # Cleanup
        db.db_manager.engine.dispose()
        os.unlink(temp_file.name)


if __name__ == "__main__":
    main()
