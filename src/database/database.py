from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
from .models import Base, Group, User
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for database operations"""

    def __init__(self, database_url: str):
        """
        Initialize database manager

        Args:
            database_url: Database connection URL
        """
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def create_tables(self):
        """Create all tables in the database"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    def close_session(self, session: Session):
        """Close database session"""
        session.close()


class GroupDatabase:
    """Class for working with groups and users database"""

    def __init__(self, database_url: str):
        """
        Initialize groups and users database

        Args:
            database_url: Database connection URL
        """
        self.db_manager = DatabaseManager(database_url)
        self.db_manager.create_tables()

    def create_group(
        self, name: str, user_ids: List[int] = None, description: str = None
    ) -> dict:
        """
        Create group with parameters

        Args:
            name: Group name
            user_ids: List of telegram_id users to add to the group
            description: Group description

        Returns:
            Dictionary with created group data

        Raises:
            ValueError: If group with this name already exists
        """
        session = self.db_manager.get_session()
        try:
            # Check if group with this name already exists
            existing_group = session.query(Group).filter(Group.name == name).first()
            if existing_group:
                raise ValueError(f"Group with name '{name}' already exists")

            # Create new group
            group = Group(name=name, description=description)
            session.add(group)
            session.flush()  # Get group ID

            # Add users to the group
            users_count = 0
            if user_ids:
                for telegram_id in user_ids:
                    user = (
                        session.query(User)
                        .filter(User.telegram_id == telegram_id)
                        .first()
                    )
                    if user:
                        group.users.append(user)
                        users_count += 1
                    else:
                        logger.warning(f"User with telegram_id {telegram_id} not found")

            session.commit()

            # Return dictionary with group data
            group_data = {
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "users_count": users_count,
                "created_at": group.created_at,
            }

            logger.info(f"Group '{name}' created successfully")
            return group_data

        except Exception as e:
            session.rollback()
            logger.error(f"Error creating group: {e}")
            raise
        finally:
            self.db_manager.close_session(session)

    def delete_group(self, group_id: int) -> bool:
        """
        Delete group

        Args:
            group_id: Group ID to delete

        Returns:
            True if group deleted, False if group not found
        """
        session = self.db_manager.get_session()
        try:
            group = session.query(Group).filter(Group.id == group_id).first()
            if not group:
                logger.warning(f"Group with ID {group_id} not found")
                return False

            session.delete(group)
            session.commit()
            logger.info(f"Group '{group.name}' deleted successfully")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting group: {e}")
            raise
        finally:
            self.db_manager.close_session(session)

    def add_user_to_group(self, group_id: int, telegram_id: int) -> bool:
        """
        Add user to group

        Args:
            group_id: Group ID
            telegram_id: User's Telegram ID

        Returns:
            True if user added, False if group or user not found
        """
        session = self.db_manager.get_session()
        try:
            group = session.query(Group).filter(Group.id == group_id).first()
            if not group:
                logger.warning(f"Group with ID {group_id} not found")
                return False

            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                logger.warning(f"User with telegram_id {telegram_id} not found")
                return False

            # Check if user is already in the group
            if user in group.users:
                logger.info(f"User {telegram_id} is already in group '{group.name}'")
                return True

            group.users.append(user)
            session.commit()
            logger.info(f"User {telegram_id} added to group '{group.name}'")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error adding user to group: {e}")
            raise
        finally:
            self.db_manager.close_session(session)

    def remove_user_from_group(self, group_id: int, telegram_id: int) -> bool:
        """
        Remove user from group

        Args:
            group_id: Group ID
            telegram_id: User's Telegram ID

        Returns:
            True if user removed, False if group or user not found
        """
        session = self.db_manager.get_session()
        try:
            group = session.query(Group).filter(Group.id == group_id).first()
            if not group:
                logger.warning(f"Group with ID {group_id} not found")
                return False

            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                logger.warning(f"User with telegram_id {telegram_id} not found")
                return False

            # Check if user is in the group
            if user not in group.users:
                logger.warning(f"User {telegram_id} is not in group '{group.name}'")
                return False

            group.users.remove(user)
            session.commit()
            logger.info(f"User {telegram_id} removed from group '{group.name}'")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error removing user from group: {e}")
            raise
        finally:
            self.db_manager.close_session(session)

    def get_all_users(self) -> List[dict]:
        """
        Get list of all users with group counts

        Returns:
            List of dictionaries with user data
        """
        session = self.db_manager.get_session()
        try:
            users = session.query(User).all()
            result = []
            for user in users:
                user_data = {
                    "id": user.id,
                    "telegram_id": user.telegram_id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                    "groups_count": len(user.groups),  # Access while session is active
                }
                result.append(user_data)
            logger.info(f"Retrieved {len(users)} users")
            return result
        except Exception as e:
            logger.error(f"Error getting user list: {e}")
            raise
        finally:
            self.db_manager.close_session(session)

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[dict]:
        """
        Get user by Telegram ID with group information

        Args:
            telegram_id: User's Telegram ID

        Returns:
            Dictionary with user data or None if not found
        """
        session = self.db_manager.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return None

            # Load related objects while session is active
            groups = []
            for group in user.groups:
                groups.append(
                    {
                        "id": group.id,
                        "name": group.name,
                        "description": group.description,
                    }
                )

            user_data = {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "groups": groups,
                "groups_count": len(groups),
            }

            return user_data
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            raise
        finally:
            self.db_manager.close_session(session)

    def create_user(
        self,
        telegram_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None,
    ) -> User:
        """
        Create new user

        Args:
            telegram_id: User's Telegram ID
            username: Telegram username
            first_name: First name
            last_name: Last name

        Returns:
            Created user

        Raises:
            ValueError: If user with this telegram_id already exists
        """
        session = self.db_manager.get_session()
        try:
            # Check if user with this telegram_id already exists
            existing_user = (
                session.query(User).filter(User.telegram_id == telegram_id).first()
            )
            if existing_user:
                raise ValueError(f"User with telegram_id {telegram_id} already exists")

            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            session.add(user)
            session.commit()
            session.refresh(user)  # Refresh object after commit
            logger.info(f"User with telegram_id {telegram_id} created successfully")
            return user

        except Exception as e:
            session.rollback()
            logger.error(f"Error creating user: {e}")
            raise
        finally:
            self.db_manager.close_session(session)

    def get_all_groups(self) -> List[dict]:
        """
        Get list of all groups with user counts

        Returns:
            List of dictionaries with group data
        """
        session = self.db_manager.get_session()
        try:
            groups = session.query(Group).all()
            result = []
            for group in groups:
                group_data = {
                    "id": group.id,
                    "name": group.name,
                    "description": group.description,
                    "created_at": group.created_at,
                    "updated_at": group.updated_at,
                    "users_count": len(group.users),  # Access while session is active
                }
                result.append(group_data)
            logger.info(f"Retrieved {len(groups)} groups")
            return result
        except Exception as e:
            logger.error(f"Error getting group list: {e}")
            raise
        finally:
            self.db_manager.close_session(session)

    def get_group_by_id(self, group_id: int) -> Optional[dict]:
        """
        Get group by ID

        Args:
            group_id: Group ID

        Returns:
            Dictionary with group data or None if not found
        """
        session = self.db_manager.get_session()
        try:
            group = session.query(Group).filter(Group.id == group_id).first()
            if not group:
                return None

            # Load related objects
            users = []
            for user in group.users:
                users.append(
                    {
                        "id": user.id,
                        "telegram_id": user.telegram_id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    }
                )

            group_data = {
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "users": users,
                "users_count": len(users),
                "created_at": group.created_at,
                "updated_at": group.updated_at,
            }

            return group_data
        except Exception as e:
            logger.error(f"Error getting group: {e}")
            raise
        finally:
            self.db_manager.close_session(session)

    def get_group_by_name(self, name: str) -> Optional[dict]:
        """
        Get group by name with user information

        Args:
            name: Group name

        Returns:
            Dictionary with group data or None if not found
        """
        session = self.db_manager.get_session()
        try:
            group = session.query(Group).filter(Group.name == name).first()
            if not group:
                return None

            # Load related objects while session is active
            users = []
            for user in group.users:
                users.append(
                    {
                        "id": user.id,
                        "telegram_id": user.telegram_id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    }
                )

            group_data = {
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "users": users,
                "users_count": len(users),
                "created_at": group.created_at,
                "updated_at": group.updated_at,
            }

            return group_data
        except Exception as e:
            logger.error(f"Error getting group: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
