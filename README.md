# telegram-agent-mcp

This repo implements proxy server that allows to access LLM Agent integrated with MCP tools


## Development

### Envs

Setup `.env` file from the `.env.example`

You can use `mysql` for the `STORAGE_DB`.

> [!IMPORTANT]
> Use `mysql` only for development since it keeps all data in memory  

### Setup

```
uv sync --dev
```


### Run

```
uv run --env-file .env src/main
```

### Tests

```
uv run pytest -vs
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
