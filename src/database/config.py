import os

class DatabaseConfig:
    """Конфигурация для подключения к базе данных"""
    
    def __init__(self):
        self.database_url = self._get_database_url()
    
    def _get_database_url(self) -> str:
        """
        Получение URL подключения к базе данных из переменных окружения
        
        Returns:
            URL подключения к базе данных
        """
        # Проверяем переменные окружения
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'school_db')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        
        # Если указан полный URL, используем его
        if os.getenv('DATABASE_URL'):
            return os.getenv('DATABASE_URL')
        
        # Формируем URL подключения
        if db_password:
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            return f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"
    
    @property
    def url(self) -> str:
        """URL подключения к базе данных"""
        return self.database_url


# Глобальный экземпляр конфигурации
db_config = DatabaseConfig() 