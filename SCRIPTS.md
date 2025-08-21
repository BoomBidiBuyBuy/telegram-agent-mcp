# System Management

## run.sh - Automatic Startup

Automatically configures and starts the entire system.

### What it does:

1. **Environment Setup**
   - Loads variables from `.env`
   - Creates database if needed

2. **Dependencies**
   - Installs dependencies with `uv sync`

3. **Services**
   - Starts MCP services in background
   - Launches main application

### Usage:

```bash
./run.sh
```

### Requirements:

- PostgreSQL running
- Python 3.12+
- `uv` package manager

### Stop:

Press `Ctrl+C` to stop all services.
