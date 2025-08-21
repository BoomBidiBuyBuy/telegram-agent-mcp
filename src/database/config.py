import os


class DatabaseConfig:
    """Database connection configuration"""

    def __init__(self):
        self.database_url = self._get_database_url()

    def _get_database_url(self) -> str:
        """
        Get database connection URL from environment variables

        Returns:
            Database connection URL
        """
        # Check environment variables
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "group_db")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "")

        # If full URL is specified, use it
        if os.getenv("DATABASE_URL"):
            return os.getenv("DATABASE_URL")

        # Build connection URL
        if db_password:
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            return f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"

    @property
    def url(self) -> str:
        """Database connection URL"""
        return self.database_url


# Global configuration instance
db_config = DatabaseConfig()
