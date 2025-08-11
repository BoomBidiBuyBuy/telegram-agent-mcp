import os


TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

STORAGE_DB = os.environ.get("STORAGE_DB", "mysql")

PG_USER = os.environ.get("PG_USER")
PG_PASSWORD = os.environ.get("PG_PASSWORD")
PG_HOST = os.environ.get("PG_HOST")
PG_PORT = os.environ.get("PG_PORT")

DEBUG_MODE = bool(int(os.environ.get("DEBUG_MODE", 0)))

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8080/mcp/")
MCP_SERVER_TRANSPORT = os.environ.get("MCP_SERVER_TRANSPORT", "streamable_http")
