#!/bin/bash

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to load environment variables
load_env() {
    if [ ! -f .env ]; then
        echo "ERROR: .env file not found"
        exit 1
    fi
    export $(grep -v '^#' .env | xargs)
}

# Function to create database
create_database() {
    if ! command_exists psql; then
        echo "WARNING: psql not found. Please install PostgreSQL client."
        echo "Database creation will be skipped."
        return
    fi
    
    if [ -n "$DB_PASSWORD" ]; then
        export PGPASSWORD="$DB_PASSWORD"
    fi
    
    if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        echo "INFO: Creating database '$DB_NAME'..."
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE \"$DB_NAME\";" >/dev/null 2>&1
    fi
    
    unset PGPASSWORD
}

# Function to cleanup on exit
cleanup() {
    if [ -f .mcp_services.pid ]; then
        MCP_PID=$(cat .mcp_services.pid)
        if kill -0 $MCP_PID 2>/dev/null; then
            kill $MCP_PID
            wait $MCP_PID 2>/dev/null
        fi
        rm -f .mcp_services.pid
    fi
}

# Set up trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Main execution
main() {
    echo "Starting Telegram Agent MCP setup and launch..."
    
    # Check if we're in the right directory
    if [ ! -f "src/main.py" ]; then
        echo "ERROR: This script must be run from the project root directory"
        exit 1 
    fi
    
    # Load environment variables
    load_env
    
    # Create database
    create_database
    
    # Install dependencies
    if ! command_exists uv; then
        echo "ERROR: uv not found. Please install uv first."
        exit 1
    fi
    uv sync
    
    # Start MCP services
    uv run --env-file .env start_mcp_services.py &
    MCP_PID=$!
    sleep 3
    
    if kill -0 $MCP_PID 2>/dev/null; then
        echo $MCP_PID > .mcp_services.pid
    else
        echo "ERROR: Failed to start MCP services"
        exit 1
    fi
    
    # Start main application
    echo "Starting main application..."
    echo "Press Ctrl+C to stop all services"
    
    uv run --env-file .env src/main.py
}

# Run main function
main "$@" 