"""Production-facing AS21 adapter over the existing task-api boundary."""
from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
import httpx
from po_agent.domain.models import Attachment, StatusTransition, Task, normalize_task_status, get_status_category
from .as21 import AS21Adapter

class AS21SourceError(RuntimeError): pass
class AS21SourceUnavailable(AS21SourceError): pass
class AS21CapabilityUnavailable(AS21SourceError): pass


def _parse_datetime(value: Any) -> datetime | None:
    if not value or not isinstance(value, str): return None
    try: return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError: return None


def _attributes(source_data: dict) -> dict[str, Any]:
    result: dict[str, Any] = {}
    raw = source_data.get("swtr_attributes", [])
    if not isinstance(raw, list): return result
    for item in raw:
        if isinstance(item, dict) and isinstance(item.get("code"), str):
            result[item["code"]] = item.get("value")
    return result


def _user_identity(value: Any) -> tuple[str | None, str | None, str | None]:
    """Map the observed AS21 user value without guessing missing identity."""
    if not isinstance(value, dict): return None, None, None
    external_id = value.get("externalId") if isinstance(value.get("externalId"), str) else None
    login = value.get("login") if isinstance(value.get("login"), str) else None
    parts = [value.get("lastName"), value.get("firstName"), value.get("middleName")]
    display = " ".join(p for p in parts if isinstance(p, str) and p.strip()) or None
    return display, external_id, login


class TaskApiAS21Adapter(AS21Adapter):
    source_name="task-api"
    # Do not advertise history/attachments until the boundary actually exposes them.
    source_facts=frozenset({"tasks"})
    def __init__(self, base_url="http://localhost:8003", *, timeout_seconds=30.0, client: httpx.AsyncClient|None=None):
        self.base_url=base_url.rstrip("/"); self._owns_client=client is None
        self._client=client or httpx.AsyncClient(base_url=self.base_url,timeout=httpx.Timeout(timeout_seconds),follow_redirects=True)

    @staticmethod
    def _map(data: dict) -> Task | None:
        source_id=data.get("source_id") or data.get("id")
        if not isinstance(source_id,str) or not source_id: return None
        source_data=data.get("source_data") if isinstance(data.get("source_data"),dict) else {}
        attrs=_attributes(source_data)
        status_raw=data.get("status") or source_data.get("workflow_status") or ""
        status=normalize_task_status(str(status_raw))
        display, external_id, login=_user_identity(attrs.get("assigned_to"))
        # Preserve top-level display name if task-api already normalized it.
        assignee=data.get("assignee") if isinstance(data.get("assignee"),str) else display
        title=data.get("title")
        if not isinstance(title,str) or not title.strip(): return None
        created=_parse_datetime(data.get("created_at")) or datetime.now()
        updated=_parse_datetime(data.get("updated_at")) or created
        return Task(key=source_id,id=source_id,title=title,description=data.get("description"),status=status,status_raw=str(status_raw) or None,status_category=get_status_category(status),created_at=created,updated_at=updated,due_date=_parse_datetime(data.get("deadline")),assignee=assignee,assignee_id=external_id,assignee_login=login,source=data.get("source","swtr"),source_url=data.get("source_url"),source_data=source_data)

    async def _get_tasks(self,query:str,limit:int)->list[Task]:
        try:
            response=await self._client.get("/api/v1/tasks",params={"q":query,"limit":limit}); response.raise_for_status()
        except httpx.HTTPError as exc: raise AS21SourceUnavailable(f"task-api request failed: {type(exc).__name__}") from exc
        try: payload=response.json()
        except ValueError as exc: raise AS21SourceError("task-api returned invalid JSON") from exc
        if not isinstance(payload,list): raise AS21SourceError("task-api /api/v1/tasks must return a JSON array")
        tasks=[]
        for item in payload:
            if not isinstance(item,dict): raise AS21SourceError("task-api returned a non-object task item")
            try: mapped=self._map(item)
            except Exception as exc: raise AS21SourceError("task-api task item cannot be mapped to canonical Task") from exc
            if mapped is None: raise AS21SourceError("task-api task item cannot be mapped to canonical Task")
            tasks.append(mapped)
        return tasks

    async def get_task(self,task_key:str)->Optional[Task]:
        normalized=task_key.upper().strip()
        return next((t for t in await self._get_tasks(normalized,10) if t.key.upper()==normalized),None)
    async def search_tasks(self,jql:str,max_results:int=50,fields:Optional[list[str]]=None)->list[Task]:
        del fields; return await self._get_tasks(jql,max_results)
    async def get_sprint_tasks(self,sprint_id:str,space:Optional[str]=None)->list[Task]:
        raise AS21CapabilityUnavailable("task-api sprint source contract is not proven yet; do not emulate JQL through simple q search")
    async def get_release_tasks(self,release_id:str,space:Optional[str]=None)->list[Task]:
        raise AS21CapabilityUnavailable("task-api release source contract is not proven yet; do not emulate JQL through simple q search")
    async def get_task_history(self,task_key:str)->list[StatusTransition]:
        raise AS21CapabilityUnavailable(f"task-api does not expose status history for {task_key}")
    async def get_attachment_metadata(self,task_key:str,attachment_id:Optional[str]=None)->list[Attachment]:
        raise AS21CapabilityUnavailable(f"task-api does not expose attachment metadata for {task_key}")
    async def close(self):
        if self._owns_client: await self._client.aclose()
