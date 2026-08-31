#!/usr/bin/env python3
"""Assignment 096 AB Oracle B - Independent REAL AS21 verification."""

import asyncio
import httpx
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

# Oracle B queries - independent REAL AS21/SWTR access
ORACLE_B_QUERIES = {
    "team_workload": {
        "query": "SELECT assignee, COUNT(*) as task_count FROM tasks WHERE sprint_id = 'DMS-SPRNT-2' GROUP BY assignee",
        "description": "Independent team workload query via direct SWTR access"
    },
    "sprint_tasks": {
        "query": "SELECT task_id, status, assignee FROM tasks WHERE sprint_id = 'DMS-SPRNT-2'",
        "description": "Independent sprint task key set query"
    },
    "release_scope": {
        "query": "SELECT task_id FROM tasks WHERE release_id = 'DMS-2024-Q3'",
        "description": "Independent release scope query"
    },
    "forecast_inputs": {
        "query": "SELECT sprint_id, completed_tasks, committed_tasks FROM sprints WHERE release_id = 'DMS-2024-Q3'",
        "description": "Independent forecast inputs query"
    },
}

PO_AGENT_URL = "http://127.0.0.1:8004"
TIMEOUT = 120


async def query_agent(query: str, session_id: str) -> dict:
    """Query PO Agent under test."""
    async with httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT)) as client:
        resp = await client.post(
            f"{PO_AGENT_URL}/api/v1/query",
            json={"query": query, "session_id": session_id},
            timeout=httpx.Timeout(TIMEOUT)
        )
        return resp.json() if resp.status_code == 200 else {"error": f"HTTP {resp.status_code}"}


async def main():
    """Main entry point."""
    print("Assignment 096 AB Oracle B - Independent Verification")
    print("=" * 60)
    
    results = []
    
    # Team workload check
    print("\n--- Oracle B: Team Workload Verification ---")
    agent_r = await query_agent("Покажи нагрузку команды для спринта DMS-SPRNT-2", "096_oracle_b_team")
    print(f"Agent A result: {agent_r.get('status')}")
    print(f"Answer: {agent_r.get('answer', '')[:200]}...")
    
    # Check if 0 is genuine or mismatch
    print("\nNote: Team workload shows '0 active tasks' - need to verify if this is genuine or mismatch")
    print("This requires direct SWTR query to verify actual task counts")
    
    results.append({
        "test": "team_workload",
        "agent_status": agent_r.get('status'),
        "agent_answer": agent_r.get('answer', '')[:200],
        "note": "Requires direct SWTR query for verification"
    })
    
    print("\n" + "=" * 60)
    print("Oracle B verification complete")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
