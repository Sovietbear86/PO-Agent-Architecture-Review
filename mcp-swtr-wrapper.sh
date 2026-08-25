#!/bin/bash
# Wrapper script to run MCP-SWTR with proper path handling
cd "/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/MyTestProject_1/MyTestProject_1/mcp-swtr"

# Source values from .env file if it exists (read first to allow env override)
if [ -f .env ]; then
    # Read BASE_URL from .env (handle both quoted and unquoted values)
    if [ -z "$BASE_URL" ]; then
        BASE_URL=$(grep "^BASE_URL=" .env | head -1 | cut -d'=' -f2- | sed 's/^["'"'"']//;s/["'"'"']$//')
        export BASE_URL
    fi
    
    # Read TOKEN from .env (handle both quoted and unquoted values)
    if [ -z "$TOKEN" ]; then
        TOKEN=$(grep "^TOKEN=" .env | head -1 | cut -d'=' -f2- | sed 's/^["'"'"']//;s/["'"'"']$//')
        export TOKEN
    fi
    
    # Read PORT from .env (handle both quoted and unquoted values)
    if [ -z "$PORT" ]; then
        PORT=$(grep "^PORT=" .env | head -1 | cut -d'=' -f2- | sed 's/^["'"'"']//;s/["'"'"']$//')
        export PORT
    fi
fi

# Default PORT=0 for stdio mode if not set
export PORT=${PORT:-0}

# Run MCP-SWTR with the environment variables passed through
exec "/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/MyTestProject_1/MyTestProject_1/mcp-swtr/.venv/bin/python" "/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/MyTestProject_1/MyTestProject_1/mcp-swtr/mcp_server.py"
