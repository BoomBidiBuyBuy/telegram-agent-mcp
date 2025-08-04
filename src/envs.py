import os


TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

STORAGE_DB = os.environ.get("STORAGE_DB", "mysql")

PG_USER = os.environ.get("PG_USER")
PG_PASSWORD = os.environ.get("PG_PASSWORD")
PG_HOST = os.environ.get("PG_HOST")
PG_PORT = os.environ.get("PG_PORT")

DEBUG_MODE = bool(int(os.environ.get("DEBUG_MODE", 0)))

PORT = os.environ.get("PORT")
WEBHOOK_PORT = os.environ.get("WEBHOOK_PORT")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
