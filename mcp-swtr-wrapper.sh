#!/usr/bin/env bash
# Portable wrapper for launching the local MCP-SWTR server over stdio.
# Community build: credentials come only from environment or an explicit MCP .env.
# No workstation-specific secret files are consulted.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="${SWTR_MCP_SERVER_DIR:-${SCRIPT_DIR}/mcp-swtr}"

if [[ ! -d "${SERVER_DIR}" ]]; then
  echo "MCP-SWTR server directory not found: ${SERVER_DIR}" >&2
  exit 2
fi

cd "${SERVER_DIR}"

# Load selected values from the MCP server .env only when the caller did not
# already provide them. Do not source arbitrary shell from .env.
if [[ -f .env ]]; then
  _env_value() {
    local key="$1"
    grep "^${key}=" .env | head -1 | cut -d'=' -f2- | sed 's/^["'"'"']//;s/["'"'"']$//'
  }

  if [[ -z "${BASE_URL:-}" ]]; then
    BASE_URL="$(_env_value BASE_URL || true)"
  fi
  if [[ -z "${TOKEN:-}" ]]; then
    TOKEN="$(_env_value TOKEN || true)"
  fi
fi

# Accept the Task API canonical variable names as fallbacks.
if [[ -z "${BASE_URL:-}" && -n "${SWTR_MCP_BASE_URL:-}" ]]; then
  BASE_URL="${SWTR_MCP_BASE_URL}"
fi
if [[ -z "${TOKEN:-}" && -n "${SWTR_TOKEN:-}" ]]; then
  TOKEN="${SWTR_TOKEN}"
fi

if [[ -z "${TOKEN:-}" ]]; then
  echo "MCP-SWTR TOKEN is not configured (TOKEN, SWTR_TOKEN or explicit MCP .env)" >&2
  exit 3
fi

if [[ -z "${BASE_URL:-}" ]]; then
  echo "MCP-SWTR BASE_URL is not configured (BASE_URL or SWTR_MCP_BASE_URL)" >&2
  exit 4
fi

export TOKEN
export BASE_URL
export PORT="${PORT:-0}"

if [[ -x "${SERVER_DIR}/.venv/bin/python" ]]; then
  PYTHON_BIN="${SERVER_DIR}/.venv/bin/python"
else
  PYTHON_BIN="${PYTHON_BIN:-python3}"
fi

exec "${PYTHON_BIN}" "${SERVER_DIR}/mcp_server.py"
