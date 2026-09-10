"""Small read-only entity resolver facade for skill-native Agent Core v4.

The endpoint deliberately reuses the already-proven MCP-SWTR identity resolver
used by the live assignee task route.  It contains no configured people and does
not consult the local task database.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.swtr_mcp_client import SWTRMCPClient
from app.routers.swtr_assignee import _resolve_external_id

router = APIRouter(prefix="/api/v1/swtr-read", tags=["swtr-read"])


@router.get("/assignees/resolve")
async def resolve_assignee(
    reference: str = Query(..., min_length=1, max_length=160),
):
    """Resolve a natural human reference to one canonical REAL AS21 user code.

    `search_users` remains the authority.  Zero/multiple candidates fail closed
    in `_resolve_external_id`; the agent never has to know a person's name in
    production routing/configuration in order to discover the source identity.
    """
    client = SWTRMCPClient()
    external_id = await _resolve_external_id(client, reference)
    return {
        "reference": reference,
        "external_id": external_id,
        "source": "REAL_AS21",
        "route": "search_users",
    }
