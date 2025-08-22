# Telegram Agent MCP

A Telegram bot with LLM agent capabilities, integrated with MCP (Model Context Protocol) services for database management and message sending.

## Features

- 🤖 **Telegram Bot** - User interaction via Telegram
- 🧠 **LLM Agent** - OpenAI GPT-powered conversation processing
- 🗄️ **Database Service** - Group and user management
- 📤 **Reply Service** - External message sending capabilities
- 🔄 **MCP Integration** - Modular service architecture

## Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# - TELEGRAM_BOT_TOKEN
# - OPENAI_API_KEY
# - Database credentials
```



### 2. Run System

```bash
./run.sh
```

The script will automatically:
- ✅ Load environment variables
- ✅ Create database if needed
- ✅ Install dependencies
- ✅ Start MCP services
- ✅ Launch main application

Press `Ctrl+C` to stop all services.


## Usage

After starting the system, send messages to your Telegram bot:

- `Create group "My Group" with users [123456789, 987654321]`
- `Show all groups`
- `Add user 123456789 to group "My Group"`
- `Show group info "My Group"`
- `Create user with Telegram ID 123456789, username @username`
- `Show all users`

## MCP Services

### Database Service
- Group management (create, delete, list)
- User management (create, list, add to groups)
- PostgreSQL database integration

### Reply Service
- Send messages to specific Telegram users
- External API integration

## Development

### Code Quality Tools

The project uses **Ruff** for code formatting and linting:

```bash
# Format code
uv run ruff format .

# Check code style and find issues
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .

# Run both formatting and linting
uv run ruff format . && uv run ruff check .
```

### Testing

```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run specific test file
uv run pytest test/test_database.py
```

## Project Structure

```
telegram-agent-mcp/
├── mcp_servers/               # MCP services
│   ├── reply_service/         # Telegram message sending
│   └── database_service/      # Database operations
├── src/                       # Core application
│   ├── agent.py              # LLM agent with MCP integration
│   ├── main.py               # Telegram bot main application
│   ├── database/             # Database module
│   │   ├── __init__.py       # Module exports
│   │   ├── database.py       # Database operations
│   │   ├── models.py         # SQLAlchemy models
│   │   └── config.py         # Database configuration
│   ├── models.py             # Legacy models (deprecated)
│   ├── config.py             # Legacy config (deprecated)
│   ├── storage.py            # Storage management
│   ├── user.py               # User management
│   └── envs.py               # Environment variables
├── assets/
│   └── mcp-servers.json      # MCP services configuration
└── run.sh                    # Startup script
```