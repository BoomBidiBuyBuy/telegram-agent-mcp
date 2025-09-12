import os

# endpoint where the users-groups-mcp-server lives
USERS_GROUPS_MCP_ENDPOINT = os.environ.get("USERS_GROUPS_MCP_ENDPOINT")

MCP_REGISTRY_ENDPOINT = os.environ.get("MCP_REGISTRY_ENDPOINT")

# Teacher Telegram ID
TEACHER_TELEGRAM_ID = int(os.environ.get("TEACHER_TELEGRAM_ID", "0"))

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# tests set 1 by default in conftest.py
# it add more output, for example SQL queries to db
DEBUG_MODE = bool(int(os.environ.get("DEBUG_MODE", "0")))

STORAGE_DB = os.environ.get("STORAGE_DB", "sqlite-memory")

# endpoint where the agentic-worker lives
AGENT_ENDPOINT = os.environ.get("AGENT_ENDPOINT")

############
# postgres #
############
PG_USER = os.environ.get("PG_USER")
PG_PASSWORD = os.environ.get("PG_PASSWORD")
PG_HOST = os.environ.get("PG_HOST")
PG_PORT = os.environ.get("PG_PORT")

# how to get events: 'polling' or 'webhook'
COMMUNICATION_MODE = os.environ.get("COMMUNICATION_MODE", "polling")

###########
# webhook #
###########

# webhook port, can be only 80, 88, 443 or 8443
# can have different value only in case of proxy
WEBHOOK_PORT = os.environ.get("WEBHOOK_PORT", os.environ.get("PORT", 8443))

# webhook url to get messages
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# ip / domain that listens for webhooks
WEBHOOK_LISTEN = os.environ.get("WEBHOOK_LISTEN")


# path to the private.key
# can be optional if set on a proxy
SSL_KEY_PATH = os.environ.get("SSL_KEY_PATH")

# path to the cert.pem
# can be optional if set on a proxy
SSL_CERT_PATH = os.environ.get("SSL_CERT_PATH")
