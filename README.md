# Telegram Agent MCP

A simplified Telegram bot with MCP (Model Context Protocol) for local development and debugging.

This repository implements a proxy server that allows access to an LLM Agent integrated with MCP tools.

## Features

- 🤖 **LLM Agent Integration**: Powered by OpenAI GPT models
- 🛠️ **MCP Tools**: Custom tools for calculations, date/time, and more
- 📱 **Telegram Bot**: Easy-to-use interface
- 🔧 **Local Development**: Simple setup for debugging and testing
- 🚀 **FastMCP Server**: Built-in MCP server with SSE transport

## Development

### Prerequisites

- Python 3.12+
- `uv` package manager
- OpenAI API key
- Telegram Bot Token

### Environment Setup

1. Create `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

2. Fill in the required environment variables:
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini  # optional
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

The MCP server will automatically start in the background on port 8080 using SSE (Server-Sent Events) transport.

## Available Tools

The MCP server provides the following tools:

- `add(a: int, b: int) -> int` - Adds two numbers together
- `current_date() -> str` - Returns current date and time with timezone
- `sleep(num_sec: int) -> None` - Sleeps for specified number of seconds
- `kid_name() -> str` - Returns a kid's name
- `get_config() -> dict` - Provides application configuration

## Usage

1. Find your bot in Telegram
2. Send `/start` command
3. Send any message, and the bot will process it using LLM and available tools

## Project Structure

- `src/agent.py` - LangChain agent connecting to MCP server
- `src/mcp_tools.py` - FastMCP server with tools
- `src/main.py` - Telegram bot with message handlers
- `src/storage.py` - Database storage layer
- `src/user.py` - User management
- `src/envs.py` - Environment configuration

## Adding New Tools

To add new tools, edit the `start_mcp_server()` function in `src/mcp_tools.py`:

```python
@mcp_server.tool
def your_new_tool(param: str) -> str:
    """Description of your tool"""
    return "result"
```

## Debugging

### Check MCP Server Status

Test if the MCP server is running:
```bash
curl http://localhost:8080/sse
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

1. **MCP Server**: FastMCP server runs in background with custom tools
2. **LangChain Agent**: Connects to MCP server and processes user messages
3. **Telegram Bot**: Handles user interactions and forwards messages to agent
4. **LLM Integration**: OpenAI GPT processes messages and decides which tools to use

## Example Interaction

User: *"Add 5 and 3"*

1. LLM understands the request
2. Calls `add(5, 3)` tool
3. Gets result `8`
4. Responds: *"The result of adding 5 and 3 is 8"*

## Troubleshooting

### ModuleNotFoundError
If you get `ModuleNotFoundError`, make sure you're using `uv run`:
```bash
uv run --env-file .env src/main.py
```

### Event Loop Error
The agent uses async/await properly to avoid event loop conflicts.

### Transport Error
The MCP server uses SSE transport which is supported by FastMCP.
