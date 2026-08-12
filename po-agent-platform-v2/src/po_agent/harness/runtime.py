"""Executable recovery Harness Core.

Business behavior is expressed as versioned skills invoking allow-listed
capabilities. The runtime is intentionally deterministic until the contracts are
stable; an LLM may later assist semantic routing and interpretation, never
replace metric calculations or source evidence.
"""
from __future__ import annotations
import re, time, uuid
from dataclasses import dataclass
from typing import Awaitable, Callable
from po_agent.adapters.as21 import AS21Adapter
from po_agent.adapters.fake import FakeAS21Adapter
from po_agent.domain.models import Task
from .contracts import CapabilityResult, Evidence, HarnessRequest, HarnessResponse, ResponseStatus

CapabilityHandler = Callable[[dict[str, str]], Awaitable[CapabilityResult]]

@dataclass(frozen=True)
class ExecutableSkill:
    id: str; version: str; intent: str; capability_id: str; description: str

class CapabilityRegistry:
    def __init__(self): self._handlers: dict[str, CapabilityHandler] = {}
    def register(self, capability_id: str, handler: CapabilityHandler):
        if capability_id in self._handlers: raise ValueError(f"Capability already registered: {capability_id}")
        self._handlers[capability_id] = handler
    async def execute(self, capability_id: str, arguments: dict[str, str]):
        if capability_id not in self._handlers: raise ValueError(f"Capability is not allow-listed: {capability_id}")
        return await self._handlers[capability_id](arguments)

class SkillRegistry:
    def __init__(self): self._by_intent: dict[str, ExecutableSkill] = {}
    def register(self, skill: ExecutableSkill):
        if skill.intent in self._by_intent: raise ValueError(f"Intent already has an active skill: {skill.intent}")
        self._by_intent[skill.intent] = skill
    def resolve(self, intent: str):
        if intent not in self._by_intent: raise ValueError(f"No active skill for intent: {intent}")
        return self._by_intent[intent]
    def catalog(self): return list(self._by_intent.values())

class PortfolioCapabilities:
    def __init__(self, adapter: AS21Adapter): self.a = adapter
    @staticmethod
    def task(t: Task):
        return {"key":t.key,"id":t.id,"title":t.title,"description":t.description,"status":t.status.value,"status_category":t.status_category.value,"assignee":t.assignee,"priority":t.priority.value if t.priority else None,"source":t.source}
    async def task_lookup(self,a):
        key=a["task_key"].upper(); t=await self.a.get_task(key)
        if not t: return CapabilityResult(answer=f"Задача {key} не найдена.",data={"task_key":key,"found":False},evidence=[Evidence(type="task_lookup",source="as21",entity_id=key,label="lookup",value="not_found")])
        return CapabilityResult(answer=f"{t.key} — {t.title}. Статус: {t.status.value}. Исполнитель: {t.assignee or 'не назначен'}.",data={"task":self.task(t)},evidence=[Evidence(type="task",source="as21",entity_id=t.key,label="title",value=t.title),Evidence(type="task",source="as21",entity_id=t.key,label="status",value=t.status.value)])
    async def task_search(self,a):
        phrase=a["phrase"].strip(); needle=phrase.casefold(); tasks=await self.a.search_tasks("")
        matches=[t for t in tasks if needle in t.key.casefold() or needle in t.title.casefold() or needle in (t.description or '').casefold()]
        return CapabilityResult(answer=f"Найдено задач: {len(matches)}.",data={"query":phrase,"count":len(matches),"tasks":[self.task(t) for t in matches]},evidence=[Evidence(type="task",source="as21",entity_id=t.key,label=t.title,value=t.status.value) for t in matches])
    async def sprint_health(self,a):
        sid=a["sprint_id"].upper(); tasks=await self.a.get_sprint_tasks(sid); total=len(tasks); done=sum(t.is_completed for t in tasks); blocked=sum(t.is_blocked for t in tasks); active=sum(t.status_category.value=="active_work" for t in tasks)
        ratio=round(done/total*100,1) if total else 0.0
        return CapabilityResult(answer=f"{sid}: выполнено {done}/{total} ({ratio}%), заблокировано {blocked}.",data={"sprint_id":sid,"total":total,"completed":done,"active":active,"blocked":blocked,"completion_percent":ratio,"tasks":[self.task(t) for t in tasks]},evidence=[Evidence(type="sprint_task",source="as21",entity_id=t.key,label=t.title,value=t.status.value) for t in tasks])
    async def release_health(self,a):
        rid=a["release_id"].upper(); tasks=await self.a.get_release_tasks(rid); total=len(tasks); done=sum(t.is_completed for t in tasks); blocked=sum(t.is_blocked for t in tasks); ratio=round(done/total*100,1) if total else 0.0
        return CapabilityResult(answer=f"{rid}: готовность {ratio}%, выполнено {done}/{total}, заблокировано {blocked}.",data={"release_id":rid,"total":total,"completed":done,"blocked":blocked,"completion_percent":ratio,"tasks":[self.task(t) for t in tasks]},evidence=[Evidence(type="release_task",source="as21",entity_id=t.key,label=t.title,value=t.status.value) for t in tasks])
    async def overview(self,a):
        tasks=await self.a.search_tasks(""); total=len(tasks); completed=sum(t.is_completed for t in tasks); blocked=sum(t.is_blocked for t in tasks); active=sum(t.status_category.value=="active_work" for t in tasks); unassigned=sum(t.assignee is None for t in tasks)
        risks=[self.task(t) for t in tasks if t.is_blocked or (t.priority and t.priority.value in ("Critical","Urgent") and not t.is_completed)]
        return CapabilityResult(answer=f"В контуре {total} задач: {active} в работе, {completed} завершено, {blocked} заблокировано.",data={"tasks_total":total,"active":active,"completed":completed,"blocked":blocked,"unassigned":unassigned,"risks":risks,"adapter":"fake-as21"},evidence=[Evidence(type="portfolio_task",source="as21",entity_id=t.key,label=t.title,value=t.status.value) for t in tasks])

class DeterministicRouter:
    TASK_KEY=re.compile(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+\b",re.I)
    SPRINT_KEY=re.compile(r"\b[A-Z]+-SPRNT-\d+\b",re.I)
    RELEASE_KEY=re.compile(r"\b[A-Z]+-\d{4}-Q\d+\b",re.I)
    def route(self,q):
        if m:=self.SPRINT_KEY.search(q): return "sprint_health",{"sprint_id":m.group(0)}
        if m:=self.RELEASE_KEY.search(q): return "release_health",{"release_id":m.group(0)}
        if m:=self.TASK_KEY.search(q): return "task_lookup",{"task_key":m.group(0)}
        low=q.casefold().strip()
        if any(x in low for x in ("обзор","сводк","что происходит","риски")): return "portfolio_overview",{}
        for p in ("найди ","поиск ","search ","найти "):
            if low.startswith(p): return "task_search",{"phrase":q[len(p):].strip().strip('"“”')}
        return "task_search",{"phrase":q.strip()}

class HarnessRuntime:
    def __init__(self,adapter:AS21Adapter):
        self.adapter=adapter; self.router=DeterministicRouter(); self.capabilities=CapabilityRegistry(); self.skills=SkillRegistry(); c=PortfolioCapabilities(adapter)
        specs=[("task-lookup","task_lookup","task.lookup",c.task_lookup),("task-search","task_search","task.search",c.task_search),("sprint-health","sprint_health","sprint.health",c.sprint_health),("release-health","release_health","release.health",c.release_health),("portfolio-overview","portfolio_overview","portfolio.overview",c.overview)]
        for sid,intent,cap,handler in specs:
            self.capabilities.register(cap,handler); self.skills.register(ExecutableSkill(sid,"1.0.0",intent,cap,f"Executable {intent} skill"))
    async def process(self,request:HarnessRequest):
        started=time.perf_counter(); trace=str(uuid.uuid4()); session=request.session_id or str(uuid.uuid4()); q=request.query.strip()
        if not q: return HarnessResponse(status=ResponseStatus.FAILED,trace_id=trace,session_id=session,answer="Пустой запрос.",warnings=["query_empty"],latency_ms=(time.perf_counter()-started)*1000)
        try:
            intent,args=self.router.route(q); skill=self.skills.resolve(intent); result=await self.capabilities.execute(skill.capability_id,args)
            return HarnessResponse(status=ResponseStatus.COMPLETED,trace_id=trace,session_id=session,answer=result.answer,intent=intent,skill_id=skill.id,skill_version=skill.version,data=result.data,evidence=result.evidence,warnings=result.warnings,latency_ms=(time.perf_counter()-started)*1000)
        except Exception:
            return HarnessResponse(status=ResponseStatus.FAILED,trace_id=trace,session_id=session,answer="Не удалось выполнить запрос.",warnings=["runtime_failure"],latency_ms=(time.perf_counter()-started)*1000)

def build_fake_runtime(): return HarnessRuntime(FakeAS21Adapter())
