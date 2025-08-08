# Telegram Agent MCP

A simplified Telegram bot with MCP (Model Context Protocol) for local development and debugging.

This repository implements a proxy server that allows access to an LLM Agent integrated with MCP tools.

## Features

- 🤖 **LLM Agent Integration**: Powered by OpenAI GPT models
- 🛠️ **MCP Tools**: Custom tools for calculations, date/time, and more
- 📱 **Telegram Bot**: Easy-to-use interface
- 🔧 **Local Development**: Simple setup for debugging and testing
- 🚀 **External MCP Server**: Connects to external MCP server

## Development

### Prerequisites

- Python 3.12+
- `uv` package manager
- OpenAI API key
- Telegram Bot Token
- External MCP server

### Environment Setup

1. Create `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

2. Fill in the required environment variables:
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5-nano  # optional, defaults to gpt-5-nano
```

> [!IMPORTANT]
> For development, you can use `mysql` for `STORAGE_DB` since it keeps all data in memory.

### Installation

Install dependencies:
```bash
uv sync --dev
```

### Running the Bot

Start the bot with a single command:
```bash
uv run --env-file .env src/main.py
```

The agent will automatically connect to the MCP server running on `http://localhost:8080/mcp/` with `streamable_http` transport.

## Usage

1. Find your bot in Telegram
2. Send `/start` command
3. Send any message, and the bot will process it using LLM and available tools

## Project Structure

- `src/agent.py` - LangChain agent connecting to external MCP server
- `src/main.py` - Telegram bot with message handlers
- `src/storage.py` - Database storage layer
- `src/user.py` - User management
- `src/envs.py` - Environment configuration

## Configuration

### OpenAI Settings

- **Model**: `gpt-5-nano` (default) or any other OpenAI model
- **Temperature**: `1` (configurable for creativity)
- **Streaming**: `False` (for better reliability)

### MCP Server Connection

- **URL**: `http://localhost:8080/mcp/`
- **Transport**: `streamable_http`
- **Auto-reconnect**: Yes, with error handling

## Debugging

### Check MCP Server Status

Test if the MCP server is running:
```bash
curl http://localhost:8080/mcp/
```

### Code Quality

Run linters:
```bash
uv run ruff check
```

Format code:
```bash
uv run ruff format
```

### Testing

Run tests:
```bash
uv run pytest
```

## How It Works

1. **External MCP Server**: FastMCP server runs externally with custom tools
2. **LangChain Agent**: Connects to external MCP server and processes user messages
3. **Telegram Bot**: Handles user interactions and forwards messages to agent
4. **LLM Integration**: OpenAI GPT processes messages and decides which tools to use

## Example Interaction

User: *"Add 5 and 3"*

1. LLM understands the request
2. Calls `add(5, 3)` tool via MCP server
3. Gets result `8`
4. Responds: *"The result of adding 5 and 3 is 8"*

