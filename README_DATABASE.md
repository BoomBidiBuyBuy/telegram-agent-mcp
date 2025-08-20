# Универсальная база данных для управления группами и пользователями

Этот проект содержит универсальную реализацию базы данных для управления группами и пользователями с использованием SQLAlchemy. Может использоваться для различных проектов: онлайн-школ, сообществ, команд и т.д.

## Структура проекта

```
telegram-agent-mcp/
├── src/
│   └── database/           # Пакет базы данных для групп и пользователей
│       ├── __init__.py     # Экспорт основных классов
│       ├── models.py       # Модели SQLAlchemy (Group, User)
│       ├── database.py     # Основные операции с БД
│       └── config.py       # Конфигурация подключения
├── examples/
│   └── database_usage_example.py # Пример использования базы данных
├── test/
│   └── test_database.py    # Тесты базы данных
└── README_DATABASE.md      # Документация базы данных
```

## Модели данных

### User (Пользователь)
- `id` - Уникальный идентификатор
- `telegram_id` - Telegram ID пользователя (уникальный)
- `username` - Имя пользователя в Telegram
- `first_name` - Имя
- `last_name` - Фамилия
- `created_at` - Дата создания
- `updated_at` - Дата обновления

### Group (Группа)
- `id` - Уникальный идентификатор
- `name` - Название группы (уникальное)
- `description` - Описание группы
- `created_at` - Дата создания
- `updated_at` - Дата обновления
- `users` - Связь с пользователями (many-to-many)

## Основные операции

### Инициализация

```python
from src.database import GroupDatabase, db_config

# Использование конфигурации по умолчанию
db = GroupDatabase(db_config.url)

# Или с собственным URL
db = GroupDatabase("postgresql://user:password@localhost/groups_db")
```

### Работа с пользователями

```python
# Создание пользователя
user = db.create_user(
    telegram_id=123456789,
    username="john_doe",
    first_name="John",
    last_name="Doe"
)

# Получение пользователя по Telegram ID
user = db.get_user_by_telegram_id(123456789)

# Получение всех пользователей
all_users = db.get_all_users()
```

### Работа с группами

```python
# Создание группы
group = db.create_group(
    name="Моя группа",
    user_ids=[123456789, 987654321],  # Список telegram_id
    description="Описание группы"
)

# Добавление пользователя в группу
success = db.add_user_to_group(group['id'], 123456789)

# Удаление пользователя из группы
success = db.remove_user_from_group(group['id'], 123456789)

# Получение группы по ID (возвращает словарь)
group_data = db.get_group_by_id(1)

# Получение группы по названию
group = db.get_group_by_name("Моя группа")

# Получение всех групп
all_groups = db.get_all_groups()

# Удаление группы
success = db.delete_group(group['id'])
```

## Возвращаемые данные

### Создание группы
Метод `create_group()` возвращает словарь:
```python
{
    'id': 1,
    'name': 'Моя группа',
    'description': 'Описание группы',
    'users_count': 2,
    'created_at': datetime.datetime(2024, 1, 1, 12, 0, 0)
}
```

### Получение группы
Метод `get_group_by_id()` возвращает словарь:
```python
{
    'id': 1,
    'name': 'Моя группа',
    'description': 'Описание группы',
    'users': [
        {
            'id': 1,
            'telegram_id': 123456789,
            'username': 'john_doe',
            'first_name': 'John',
            'last_name': 'Doe'
        }
    ],
    'users_count': 1,
    'created_at': datetime.datetime(2024, 1, 1, 12, 0, 0),
    'updated_at': datetime.datetime(2024, 1, 1, 12, 0, 0)
}
```

## Конфигурация

База данных настраивается через переменные окружения:

```bash
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=groups_db
DB_USER=postgres
DB_PASSWORD=your_password

# Или полный URL
DATABASE_URL=postgresql://user:password@localhost/groups_db
```

## Примеры использования

```bash
python examples/database_usage_example.py
```

## Тестирование

Для запуска тестов используйте:

```bash
pytest test/test_database.py -v
```

Тесты используют временную SQLite базу данных для изоляции.

## Требования

- Python 3.12+
- SQLAlchemy 2.0+
- PostgreSQL (рекомендуется) или SQLite
- psycopg2-binary (для PostgreSQL)

## Особенности реализации

1. **Изоляция сессий**: Каждая операция использует отдельную сессию SQLAlchemy
2. **Возврат словарей**: Вместо объектов SQLAlchemy возвращаются словари для избежания проблем с отсоединенными объектами
3. **Обработка ошибок**: Все операции включают обработку исключений и логирование
4. **Транзакционность**: Операции выполняются в транзакциях с автоматическим откатом при ошибках

## Поддерживаемые операции

✅ Создание группы с параметрами (имя, список user_id)
✅ Удаление группы
✅ Добавление пользователя в группу
✅ Удаление пользователя из группы
✅ Получение списка всех пользователей
✅ Создание пользователей
✅ Получение пользователя по Telegram ID
✅ Получение группы по ID и названию
✅ Получение всех групп 