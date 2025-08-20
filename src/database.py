from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, NoResultFound
from typing import List, Optional, Dict, Any
from .models import Base, Group, User, group_user_association
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Менеджер для работы с базой данных"""
    
    def __init__(self, database_url: str):
        """
        Инициализация менеджера БД
        
        Args:
            database_url: URL подключения к базе данных
        """
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Создание всех таблиц в базе данных"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def get_session(self) -> Session:
        """Получение сессии базы данных"""
        return self.SessionLocal()
    
    def close_session(self, session: Session):
        """Закрытие сессии базы данных"""
        session.close()


class SchoolDatabase:
    """Класс для работы с базой данных онлайн-школы"""
    
    def __init__(self, database_url: str):
        """
        Инициализация базы данных школы
        
        Args:
            database_url: URL подключения к базе данных
        """
        self.db_manager = DatabaseManager(database_url)
        self.db_manager.create_tables()
    
    def create_group(self, name: str, user_ids: List[int] = None, description: str = None) -> Group:
        """
        Создание группы с параметрами
        
        Args:
            name: Название группы
            user_ids: Список telegram_id пользователей для добавления в группу
            description: Описание группы
            
        Returns:
            Созданная группа
            
        Raises:
            ValueError: Если группа с таким именем уже существует
        """
        session = self.db_manager.get_session()
        try:
            # Проверяем, существует ли группа с таким именем
            existing_group = session.query(Group).filter(Group.name == name).first()
            if existing_group:
                raise ValueError(f"Группа с именем '{name}' уже существует")
            
            # Создаем новую группу
            group = Group(name=name, description=description)
            session.add(group)
            session.flush()  # Получаем ID группы
            
            # Добавляем пользователей в группу
            if user_ids:
                for telegram_id in user_ids:
                    user = session.query(User).filter(User.telegram_id == telegram_id).first()
                    if user:
                        group.users.append(user)
                    else:
                        logger.warning(f"Пользователь с telegram_id {telegram_id} не найден")
            
            session.commit()
            logger.info(f"Группа '{name}' создана успешно")
            return group
            
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при создании группы: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def delete_group(self, group_id: int) -> bool:
        """
        Удаление группы
        
        Args:
            group_id: ID группы для удаления
            
        Returns:
            True если группа удалена, False если группа не найдена
        """
        session = self.db_manager.get_session()
        try:
            group = session.query(Group).filter(Group.id == group_id).first()
            if not group:
                logger.warning(f"Группа с ID {group_id} не найдена")
                return False
            
            session.delete(group)
            session.commit()
            logger.info(f"Группа '{group.name}' удалена успешно")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при удалении группы: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def add_user_to_group(self, group_id: int, telegram_id: int) -> bool:
        """
        Добавление пользователя в группу
        
        Args:
            group_id: ID группы
            telegram_id: Telegram ID пользователя
            
        Returns:
            True если пользователь добавлен, False если группа или пользователь не найдены
        """
        session = self.db_manager.get_session()
        try:
            group = session.query(Group).filter(Group.id == group_id).first()
            if not group:
                logger.warning(f"Группа с ID {group_id} не найдена")
                return False
            
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                logger.warning(f"Пользователь с telegram_id {telegram_id} не найден")
                return False
            
            # Проверяем, не состоит ли пользователь уже в группе
            if user in group.users:
                logger.info(f"Пользователь {telegram_id} уже состоит в группе '{group.name}'")
                return True
            
            group.users.append(user)
            session.commit()
            logger.info(f"Пользователь {telegram_id} добавлен в группу '{group.name}'")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при добавлении пользователя в группу: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def remove_user_from_group(self, group_id: int, telegram_id: int) -> bool:
        """
        Удаление пользователя из группы
        
        Args:
            group_id: ID группы
            telegram_id: Telegram ID пользователя
            
        Returns:
            True если пользователь удален, False если группа или пользователь не найдены
        """
        session = self.db_manager.get_session()
        try:
            group = session.query(Group).filter(Group.id == group_id).first()
            if not group:
                logger.warning(f"Группа с ID {group_id} не найдена")
                return False
            
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                logger.warning(f"Пользователь с telegram_id {telegram_id} не найден")
                return False
            
            # Проверяем, состоит ли пользователь в группе
            if user not in group.users:
                logger.warning(f"Пользователь {telegram_id} не состоит в группе '{group.name}'")
                return False
            
            group.users.remove(user)
            session.commit()
            logger.info(f"Пользователь {telegram_id} удален из группы '{group.name}'")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при удалении пользователя из группы: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def get_all_users(self) -> List[User]:
        """
        Получение списка всех пользователей
        
        Returns:
            Список всех пользователей
        """
        session = self.db_manager.get_session()
        try:
            users = session.query(User).all()
            logger.info(f"Получено {len(users)} пользователей")
            return users
        except Exception as e:
            logger.error(f"Ошибка при получении списка пользователей: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Получение пользователя по Telegram ID
        
        Args:
            telegram_id: Telegram ID пользователя
            
        Returns:
            Пользователь или None если не найден
        """
        session = self.db_manager.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            return user
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def create_user(self, telegram_id: int, username: str = None, 
                   first_name: str = None, last_name: str = None,
                   email: str = None, phone: str = None) -> User:
        """
        Создание нового пользователя
        
        Args:
            telegram_id: Telegram ID пользователя
            username: Имя пользователя в Telegram
            first_name: Имя
            last_name: Фамилия
            email: Email
            phone: Телефон
            
        Returns:
            Созданный пользователь
            
        Raises:
            ValueError: Если пользователь с таким telegram_id уже существует
        """
        session = self.db_manager.get_session()
        try:
            # Проверяем, существует ли пользователь с таким telegram_id
            existing_user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if existing_user:
                raise ValueError(f"Пользователь с telegram_id {telegram_id} уже существует")
            
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone
            )
            session.add(user)
            session.commit()
            logger.info(f"Пользователь с telegram_id {telegram_id} создан успешно")
            return user
            
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при создании пользователя: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def get_all_groups(self) -> List[Group]:
        """
        Получение списка всех групп
        
        Returns:
            Список всех групп
        """
        session = self.db_manager.get_session()
        try:
            groups = session.query(Group).all()
            logger.info(f"Получено {len(groups)} групп")
            return groups
        except Exception as e:
            logger.error(f"Ошибка при получении списка групп: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def get_group_by_id(self, group_id: int) -> Optional[Group]:
        """
        Получение группы по ID
        
        Args:
            group_id: ID группы
            
        Returns:
            Группа или None если не найдена
        """
        session = self.db_manager.get_session()
        try:
            group = session.query(Group).filter(Group.id == group_id).first()
            return group
        except Exception as e:
            logger.error(f"Ошибка при получении группы: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def get_group_by_name(self, name: str) -> Optional[Group]:
        """
        Получение группы по названию
        
        Args:
            name: Название группы
            
        Returns:
            Группа или None если не найдена
        """
        session = self.db_manager.get_session()
        try:
            group = session.query(Group).filter(Group.name == name).first()
            return group
        except Exception as e:
            logger.error(f"Ошибка при получении группы: {e}")
            raise
        finally:
            self.db_manager.close_session(session) 