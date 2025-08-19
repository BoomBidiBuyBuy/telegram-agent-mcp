import os


TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# tests set 1 by default in conftest.py
# it add more output, for example SQL queries to db
DEBUG_MODE = bool(int(os.environ.get("DEBUG_MODE", 0)))

STORAGE_DB = os.environ.get("STORAGE_DB", "mysql")

########################
# fastmcp server url #
########################
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8080/mcp/")
MCP_SERVER_TRANSPORT = os.environ.get("MCP_SERVER_TRANSPORT", "streamable_http")
# path to mcp servers json file (used by loader in agent)
MCP_SERVERS_FILE_PATH = os.environ.get("MCP_SERVERS_FILE_PATH", "mcp-servers.json")

#############################
# Reply Service MCP settings #
#############################
REPLY_SERVICE_MCP_HOST = os.environ.get("REPLY_SERVICE_MCP_HOST", "0.0.0.0")
REPLY_SERVICE_MCP_PORT = int(os.environ.get("REPLY_SERVICE_MCP_PORT", "8091"))

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

# path to the private.key
# can be optional if set on a proxy
SSL_KEY_PATH = os.environ.get("SSL_KEY_PATH")

# path to the cert.pem
# can be optional if set on a proxy
SSL_CERT_PATH = os.environ.get("SSL_CERT_PATH")
