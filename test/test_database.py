"""
Тесты для базы данных онлайн-школы
"""

import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import GroupDatabase, Group, User


@pytest.fixture
def temp_db():
    """Фикстура для создания временной базы данных"""
    # Создаем временный файл для SQLite базы данных
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    # URL для SQLite базы данных
    database_url = f"sqlite:///{temp_file.name}"
    
    # Создаем экземпляр базы данных
    db = GroupDatabase(database_url)
    
    yield db
    
    # Очистка после тестов
    db.db_manager.engine.dispose()
    os.unlink(temp_file.name)


class TestGroupDatabase:
    """Тесты для класса GroupDatabase"""
    
    def test_create_user(self, temp_db):
        """Тест создания пользователя"""
        user = temp_db.create_user(
            telegram_id=123456789,
            username="test_user",
            first_name="Тест",
            last_name="Пользователь"
        )
        
        assert user.telegram_id == 123456789
        assert user.username == "test_user"
        assert user.first_name == "Тест"
        assert user.last_name == "Пользователь"
        
        # Проверяем, что пользователь действительно создан в БД
        found_user = temp_db.get_user_by_telegram_id(123456789)
        assert found_user is not None
        assert found_user.telegram_id == 123456789
    
    def test_create_duplicate_user(self, temp_db):
        """Тест создания дублирующегося пользователя"""
        # Создаем первого пользователя
        temp_db.create_user(telegram_id=123456789, username="test_user")
        
        # Пытаемся создать пользователя с тем же telegram_id
        with pytest.raises(ValueError, match="уже существует"):
            temp_db.create_user(telegram_id=123456789, username="another_user")
    
    def test_create_group(self, temp_db):
        """Тест создания группы"""
        # Создаем пользователей
        user1 = temp_db.create_user(telegram_id=111, username="user1")
        user2 = temp_db.create_user(telegram_id=222, username="user2")
        
        # Создаем группу
        group = temp_db.create_group(
            name="Тестовая группа",
            user_ids=[111, 222],
            description="Описание группы"
        )
        
        assert group.name == "Тестовая группа"
        assert group.description == "Описание группы"
        
        # Проверяем, что группа действительно создана в БД
        found_group = temp_db.get_group_by_id(group.id)
        assert found_group is not None
        assert found_group.name == "Тестовая группа"
        assert len(found_group.users) == 2
    
    def test_create_duplicate_group(self, temp_db):
        """Тест создания дублирующейся группы"""
        # Создаем первую группу
        temp_db.create_group(name="Тестовая группа")
        
        # Пытаемся создать группу с тем же именем
        with pytest.raises(ValueError, match="уже существует"):
            temp_db.create_group(name="Тестовая группа")
    
    def test_add_user_to_group(self, temp_db):
        """Тест добавления пользователя в группу"""
        # Создаем пользователя и группу
        user = temp_db.create_user(telegram_id=123, username="test_user")
        group = temp_db.create_group(name="Тестовая группа")
        
        # Добавляем пользователя в группу
        success = temp_db.add_user_to_group(group.id, 123)
        
        assert success is True
        
        # Проверяем, что пользователь действительно добавлен в группу
        found_group = temp_db.get_group_by_id(group.id)
        assert found_group is not None
        assert len(found_group.users) == 1
        assert found_group.users[0].telegram_id == 123
    
    def test_add_user_to_nonexistent_group(self, temp_db):
        """Тест добавления пользователя в несуществующую группу"""
        user = temp_db.create_user(telegram_id=123, username="test_user")
        
        # Пытаемся добавить пользователя в несуществующую группу
        success = temp_db.add_user_to_group(999, 123)
        
        assert success is False
    
    def test_add_nonexistent_user_to_group(self, temp_db):
        """Тест добавления несуществующего пользователя в группу"""
        group = temp_db.create_group(name="Тестовая группа")
        
        # Пытаемся добавить несуществующего пользователя
        success = temp_db.add_user_to_group(group.id, 999)
        
        assert success is False
        
        # Проверяем, что группа осталась пустой
        found_group = temp_db.get_group_by_id(group.id)
        assert found_group is not None
        assert len(found_group.users) == 0
    
    def test_remove_user_from_group(self, temp_db):
        """Тест удаления пользователя из группы"""
        # Создаем пользователя и группу
        user = temp_db.create_user(telegram_id=123, username="test_user")
        group = temp_db.create_group(name="Тестовая группа", user_ids=[123])
        
        # Удаляем пользователя из группы
        success = temp_db.remove_user_from_group(group.id, 123)
        
        assert success is True
        
        # Проверяем, что пользователь действительно удален из группы
        found_group = temp_db.get_group_by_id(group.id)
        assert found_group is not None
        assert len(found_group.users) == 0
    
    def test_remove_user_from_nonexistent_group(self, temp_db):
        """Тест удаления пользователя из несуществующей группы"""
        user = temp_db.create_user(telegram_id=123, username="test_user")
        
        # Пытаемся удалить пользователя из несуществующей группы
        success = temp_db.remove_user_from_group(999, 123)
        
        assert success is False
    
    def test_get_all_users(self, temp_db):
        """Тест получения всех пользователей"""
        # Создаем несколько пользователей
        user1 = temp_db.create_user(telegram_id=111, username="user1")
        user2 = temp_db.create_user(telegram_id=222, username="user2")
        user3 = temp_db.create_user(telegram_id=333, username="user3")
        
        # Получаем всех пользователей
        all_users = temp_db.get_all_users()
        
        assert len(all_users) == 3
        
        # Проверяем, что все пользователи найдены по telegram_id
        telegram_ids = [user.telegram_id for user in all_users]
        assert 111 in telegram_ids
        assert 222 in telegram_ids
        assert 333 in telegram_ids
    
    def test_get_user_by_telegram_id(self, temp_db):
        """Тест получения пользователя по telegram_id"""
        # Создаем пользователя
        created_user = temp_db.create_user(telegram_id=123, username="test_user")
        
        # Получаем пользователя по telegram_id
        found_user = temp_db.get_user_by_telegram_id(123)
        
        assert found_user is not None
        assert found_user.telegram_id == 123
        assert found_user.username == "test_user"
    
    def test_get_nonexistent_user_by_telegram_id(self, temp_db):
        """Тест получения несуществующего пользователя"""
        found_user = temp_db.get_user_by_telegram_id(999)
        
        assert found_user is None
    
    def test_get_all_groups(self, temp_db):
        """Тест получения всех групп"""
        # Создаем несколько групп
        group1 = temp_db.create_group(name="Группа 1")
        group2 = temp_db.create_group(name="Группа 2")
        group3 = temp_db.create_group(name="Группа 3")
        
        # Получаем все группы
        all_groups = temp_db.get_all_groups()
        
        assert len(all_groups) == 3
        
        # Проверяем, что все группы найдены по названию
        group_names = [group.name for group in all_groups]
        assert "Группа 1" in group_names
        assert "Группа 2" in group_names
        assert "Группа 3" in group_names
    
    def test_get_group_by_id(self, temp_db):
        """Тест получения группы по ID"""
        # Создаем группу
        created_group = temp_db.create_group(name="Тестовая группа")
        group_id = created_group.id
        
        # Получаем группу по ID
        found_group = temp_db.get_group_by_id(group_id)
        
        assert found_group is not None
        assert found_group.name == "Тестовая группа"
    
    def test_get_nonexistent_group_by_id(self, temp_db):
        """Тест получения несуществующей группы по ID"""
        found_group = temp_db.get_group_by_id(999)
        
        assert found_group is None
    
    def test_get_group_by_name(self, temp_db):
        """Тест получения группы по названию"""
        # Создаем группу
        created_group = temp_db.create_group(name="Тестовая группа")
        group_id = created_group.id
        
        # Получаем группу по названию
        found_group = temp_db.get_group_by_name("Тестовая группа")
        
        assert found_group is not None
        assert found_group.id == group_id
    
    def test_get_nonexistent_group_by_name(self, temp_db):
        """Тест получения несуществующей группы по названию"""
        found_group = temp_db.get_group_by_name("Несуществующая группа")
        
        assert found_group is None
    
    def test_delete_group(self, temp_db):
        """Тест удаления группы"""
        # Создаем группу
        group = temp_db.create_group(name="Тестовая группа")
        group_id = group.id
        
        # Удаляем группу
        success = temp_db.delete_group(group_id)
        
        assert success is True
        
        # Проверяем, что группа действительно удалена
        found_group = temp_db.get_group_by_id(group_id)
        assert found_group is None
    
    def test_delete_nonexistent_group(self, temp_db):
        """Тест удаления несуществующей группы"""
        success = temp_db.delete_group(999)
        
        assert success is False 