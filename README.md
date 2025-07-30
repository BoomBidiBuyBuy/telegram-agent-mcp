# telegram-agent-mcp

This repo implements proxy server that allows to access LLM Agent integrated with MCP tools


## Development

### Envs

Setup `.env` file from the `.env.example`


### Setup

```
uv sync --dev
```


### Run

```
uv run --env-file .env src/main
```

### Linters

```
uv run ruff check
```

and 

```
uv run ruff format
```

for formatting
