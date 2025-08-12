# Telegram Agent MCP

A simplified Telegram bot with MCP (Model Context Protocol) for local development and debugging.

This repository implements a proxy server that allows access to an LLM Agent integrated with MCP tools.

## Features

- 🤖 **LLM Agent Integration**: Powered by OpenAI GPT models
- 🛠️ **MCP Tools**: Custom tools for calculations, date/time, and more
- 📱 **Telegram Bot**: Easy-to-use interface
- 🔧 **Local Development**: Simple setup for debugging and testing
- 🚀 **Remote MCP Server**: Connects to external MCP server
- 🧠 **Conversation Memory**: Built-in memory system with InMemorySaver

## Development

### Prerequisites

- Python 3.12+
- `uv` package manager
- OpenAI API key
- Telegram Bot Token
- External MCP server

### Environment Setup

1. Create `.env` file based on `env.example`:
```bash
cp env.example .env
```

2. Fill in the required environment variables:
```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5-nano

# MCP Server Configuration
MCP_SERVER_URL=http://146.103.106.184:8080/mcp/
MCP_SERVER_TRANSPORT=streamable_http
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

The agent will automatically connect to the MCP server specified in your `.env` file.

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

- **URL**: Configurable via `MCP_SERVER_URL` environment variable
- **Transport**: Configurable via `MCP_SERVER_TRANSPORT` environment variable
- **Auto-reconnect**: Yes, with error handling

### Memory Management

- **InMemorySaver**: Built-in LangGraph memory system for conversation history
- **Thread-based isolation**: Each user has separate conversation context
- **Automatic persistence**: Conversation history is automatically maintained between messages

### Communication Modes

We support two ways of communication with the Telegram server:
- **polling**, ie when bot time to time goes to the telegram servers and checks for new messages or events
- **webhook**, ie when the bot registers its own url where the telegram server should send new messages and events

The `COMMUNICATION_MODE` env variable handles it. The **polling** is default.

#### Webhook configuration

First of all set the `COMMUNICATION_MODE` to `webhook`.

Using webhook requires setting up SSL.

This command generates `private.key` and `cert.pem` files for SSL.
```bash
openssl req -newkey rsa:2048 -sha256 -nodes -keyout private.key -x509 -days 3650 -out cert.pem
```
(use domain name / IP address when it asks for FQDN)

Then we need to define `SSL_KEY_PATH` and `SSL_CERT_PATH` env in `.env` to generated files.

The `WEBHOOK_PORT` should be set to 80, 88, 443 or 8443.

The `WEBHOOK_URL` needs to have format `https://<your-domain-or-ip>:<webhook-port>`. Port is required in the URL in this case.

### Remote MCP Server Setup

To connect to a remote MCP server:

1. **Ensure the server is accessible**:
   - Server should be bound to `0.0.0.0:8080` (not `127.0.0.1:8080`)
   - Port 8080 should be open in firewall
   - Server should support `streamable_http` transport

2. **Configure in `.env`**:
```bash
MCP_SERVER_URL=http://your-server-ip:8080/mcp/
MCP_SERVER_TRANSPORT=streamable_http
```

3. **Test connectivity**:
```bash
curl http://your-server-ip:8080/mcp/
```

## Debugging

### Tests

```bash
uv run pytest -vs
```

### Linters

Run linters:
```bash
uv run ruff check
```

Format code:
```bash
uv run ruff format
```

### Check MCP Server Status

Test if the MCP server is running:
```bash
curl $MCP_SERVER_URL
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
5. **Memory System**: InMemorySaver maintains conversation history for each user

## Example Interaction

User: *"Add 5 and 3"*

1. LLM understands the request
2. Calls `add(5, 3)` tool via MCP server
3. Gets result `8`
4. Responds: *"The result of adding 5 and 3 is 8"*

## Deployment

### Heroku

Heroku integrates only with the webhook mode.

You need to setup only the following envs on Heroku site:
- `COMMUNICATION_MODE=webhook`
- `WEBHOOK_URL=https://<your-app-id>.herokuapp.com/` (note that port should not be in the url because Heroku communicates application through a proxy)
- `TELEGRAM_BOT_TOKEN`

No need to setup `WEBHOOK_PORT`, `SSL_KEY_PATH` and `SSL_CERT_PATH` because Heroku manages SSL on their proxy side. As for the port, they assigned it through the `PORT` env variable that we use instead of `WEBHOOK_PORT` to be integrated with their approach.
