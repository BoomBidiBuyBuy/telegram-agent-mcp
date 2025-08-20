#!/usr/bin/env python3
"""
Пример использования базы данных для онлайн-школы
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import GroupDatabase
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Основная функция с примерами использования БД"""
    
    # Инициализация базы данных
    print("Инициализация базы данных...")
    # Используем SQLite для демонстрации
    import tempfile
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    database_url = f"sqlite:///{temp_file.name}"
    db = GroupDatabase(database_url)
    
    try:
        # Пример 1: Создание пользователей
        print("\n=== Создание пользователей ===")
        
        # Создаем несколько пользователей
        users_data = [
            {"telegram_id": 123456789, "username": "ivan_petrov", "first_name": "Иван", "last_name": "Петров"},
            {"telegram_id": 987654321, "username": "maria_sidorova", "first_name": "Мария", "last_name": "Сидорова"},
            {"telegram_id": 555666777, "username": "alex_kuznetsov", "first_name": "Алексей", "last_name": "Кузнецов"},
            {"telegram_id": 111222333, "username": "anna_ivanova", "first_name": "Анна", "last_name": "Иванова"},
        ]
        
        created_users = []
        for user_data in users_data:
            try:
                user = db.create_user(**user_data)
                created_users.append(user)
                print(f"Создан пользователь: {user.first_name} {user.last_name} (ID: {user.telegram_id})")
            except ValueError as e:
                print(f"Пользователь уже существует: {e}")
                # Получаем существующего пользователя
                user = db.get_user_by_telegram_id(user_data["telegram_id"])
                if user:
                    created_users.append(user)
        
        # Пример 2: Создание групп
        print("\n=== Создание групп ===")
        
        # Создаем группу для начинающих
        beginner_group = db.create_group(
            name="Начинающие английский",
            user_ids=[123456789, 987654321],
            description="Группа для изучения английского языка с нуля"
        )
        print(f"Создана группа: {beginner_group['name']} (ID: {beginner_group['id']})")
        
        # Создаем группу для продвинутых
        advanced_group = db.create_group(
            name="Продвинутый английский",
            user_ids=[555666777],
            description="Группа для продвинутого уровня английского"
        )
        print(f"Создана группа: {advanced_group['name']} (ID: {advanced_group['id']})")
        
        # Пример 3: Добавление пользователя в группу
        print("\n=== Добавление пользователя в группу ===")
        
        # Добавляем Анну в группу начинающих
        success = db.add_user_to_group(beginner_group['id'], 111222333)
        if success:
            print(f"Пользователь 111222333 добавлен в группу '{beginner_group['name']}'")
        else:
            print("Не удалось добавить пользователя в группу")
        
        # Пример 4: Получение списка всех пользователей
        print("\n=== Список всех пользователей ===")
        all_users = db.get_all_users()
        for user in all_users:
            print(f"- {user.first_name} {user.last_name} (@{user.username}, ID: {user.telegram_id})")
        
        # Пример 5: Получение информации о группах
        print("\n=== Информация о группах ===")
        all_groups = db.get_all_groups()
        for group in all_groups:
            print(f"\nГруппа: {group.name}")
            print(f"Описание: {group.description}")
            # Получаем полную информацию о группе
            group_data = db.get_group_by_id(group.id)
            if group_data:
                print(f"Количество участников: {group_data['users_count']}")
                print("Участники:")
                for user in group_data['users']:
                    print(f"  - {user['first_name']} {user['last_name']} (@{user['username']})")
            else:
                print("Количество участников: 0")
        
        # Пример 6: Удаление пользователя из группы
        print("\n=== Удаление пользователя из группы ===")
        
        # Удаляем Марию из группы начинающих
        success = db.remove_user_from_group(beginner_group['id'], 987654321)
        if success:
            print(f"Пользователь 987654321 удален из группы '{beginner_group['name']}'")
        else:
            print("Не удалось удалить пользователя из группы")
        
        # Пример 7: Поиск группы по названию
        print("\n=== Поиск группы по названию ===")
        found_group = db.get_group_by_name("Начинающие английский")
        if found_group:
            print(f"Найдена группа: {found_group.name} (ID: {found_group.id})")
            # Получаем полную информацию о группе
            group_data = db.get_group_by_id(found_group.id)
            if group_data:
                print(f"Участников: {group_data['users_count']}")
            else:
                print("Участников: 0")
        else:
            print("Группа не найдена")
        
        # Пример 8: Удаление группы
        print("\n=== Удаление группы ===")
        
        # Создаем временную группу для демонстрации удаления
        temp_group = db.create_group(
            name="Временная группа",
            description="Группа для демонстрации удаления"
        )
        print(f"Создана временная группа: {temp_group['name']} (ID: {temp_group['id']})")
        
        # Удаляем временную группу
        success = db.delete_group(temp_group['id'])
        if success:
            print(f"Группа '{temp_group['name']}' успешно удалена")
        else:
            print("Не удалось удалить группу")
        
        print("\n=== Демонстрация завершена ===")
        
    except Exception as e:
        logger.error(f"Ошибка при работе с базой данных: {e}")
        raise
    finally:
        # Очистка
        db.db_manager.engine.dispose()
        os.unlink(temp_file.name)


if __name__ == "__main__":
    main() 