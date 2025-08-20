"""
Пакет для работы с универсальной базой данных групп и пользователей
"""

from .models import Base, Group, User, group_user_association
from .database import GroupDatabase, DatabaseManager
from .config import DatabaseConfig, db_config

__all__ = [
    'Base',
    'Group', 
    'User',
    'group_user_association',
    'GroupDatabase',
    'DatabaseManager',
    'DatabaseConfig',
    'db_config'
] 