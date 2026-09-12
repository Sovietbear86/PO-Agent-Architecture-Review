#!/bin/bash
# Fresh PO Agent (Assignment 183 Phase 4) on port 8019 against fresh task-api 8013.
cd po-agent-platform-v2
source .env
unset PYTHONPATH
export PO_AGENT_AS21_MODE=task-api
export PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8013
export PO_AGENT_AGENT_CORE_V4_ENABLED=true
export PO_AGENT_EXPECTED_PACKAGE_ROOT="$(pwd)"
export PO_AGENT_EXPECTED_HEAD="$(git -C .. rev-parse HEAD)"
.venv/bin/python3 -m uvicorn po_agent.main:app --host 127.0.0.1 --port 8019 --timeout-keep-alive 120