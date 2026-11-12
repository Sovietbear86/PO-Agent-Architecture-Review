"""Run entry point for the SberProject catalog connector.

Run with an approved, operator-provisioned environment, e.g.:

    uvicorn app.services.sberproject.main:app --host 127.0.0.1 --port 8242

The connector is disabled by default; with no approved client identity it serves
a typed ``sberproject_auth_required`` / ``sberproject_source_unavailable`` state
only (it never simulates a working source). See
``task-api/docs/SBERPROJECT_CONNECTOR_RUNBOOK.md`` for configuration names and
the corporate IT approval checklist.
"""
from .connector import main

app = main()
