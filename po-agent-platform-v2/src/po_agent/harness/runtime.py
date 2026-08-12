"""Executable recovery Harness Core."""
from __future__ import annotations
import re, time, uuid
from dataclasses import dataclass
from typing import Awaitable, Callable
from po_agent.adapters.as21 import AS21Adapter
from po_agent.adapters.fake import FakeAS21Adapter
from po_agent.domain.models import AttachmentType, Task
from .contracts import CapabilityResult, Evidence, HarnessRequest, HarnessResponse, ResponseStatus
from .release_intelligence import ReleaseIntelligenceCapabilities
from .sprint_intelligence import SprintIntelligenceCapabilities
from .team_intelligence import TeamIntelligenceCapabilities
from .task_advanced import AdvancedTaskCapabilities
from .task_intelligence import TaskIntelligenceCapabilities
CapabilityHandler = Callable[[dict[str, str]], Awaitable[CapabilityResult]]
@dataclass(frozen=True)
class ExecutableSkill:
    id:str; version:str; intent:str; capability_id:str; description:str
class CapabilityRegistry:
    def __init__(self): self._handlers={}
    def register(self, capability_id, handler):
        if capability_id in self._handlers: raise ValueError(f"Capability already registered: {capability_id}")
        self._handlers[capability_id]=handler
    async def execute(self, capability_id, arguments):
        if capability_id not in self._handlers: raise ValueError(f"Capability is not allow-listed: {capability_id}")
        return await self._handlers[capability_id](arguments)
class SkillRegistry:
    def __init__(self): self._by_intent={}
    def register(self, skill):
        if skill.intent in self._by_intent: raise ValueError(f"Intent already has an active skill: {skill.intent}")
        self._by_intent[skill.intent]=skill
    def resolve(self,intent):
        if intent not in self._by_intent: raise ValueError(f"No active skill for intent: {intent}")
        return self._by_intent[intent]
    def catalog(self): return list(self._by_intent.values())
class PortfolioCapabilities:
    def __init__(self,adapter): self.a=adapter
    @staticmethod
    def task(t:Task): return {"key":t.key,"id":t.id,"title":t.title,"description":t.description,"status":t.status.value,"status_category":t.status_category.value,"assignee":t.assignee,"priority":t.priority.value if t.priority else None,"sprint_id":t.sprint_id,"release_id":t.release_id,"source":t.source}
    @classmethod
    def task_list_result(cls,*,answer,tasks,filters,evidence_type="task"): return CapabilityResult(answer=answer,data={"count":len(tasks),"filters":filters,"tasks":[cls.task(t) for t in tasks]},evidence=[Evidence(type=evidence_type,source="as21",entity_id=t.key,label=t.title,value=t.status.value) for t in tasks])
    async def task_lookup(self,args):
        key=args["task_key"].upper(); t=await self.a.get_task(key)
        if not t:return CapabilityResult(answer=f"Задача {key} не найдена.",data={"task_key":key,"found":False},evidence=[Evidence(type="task_lookup",source="as21",entity_id=key,label="lookup",value="not_found")])
        return CapabilityResult(answer=f"{t.key} — {t.title}. Статус: {t.status.value}. Исполнитель: {t.assignee or 'не назначен'}.",data={"task":self.task(t)},evidence=[Evidence(type="task",source="as21",entity_id=t.key,label="title",value=t.title),Evidence(type="task",source="as21",entity_id=t.key,label="status",value=t.status.value),Evidence(type="task",source="as21",entity_id=t.key,label="assignee",value=t.assignee)])
    async def task_search(self,args):
        p=args["phrase"].strip(); n=p.casefold(); tasks=await self.a.search_tasks(""); m=[t for t in tasks if n in t.key.casefold() or n in t.title.casefold() or n in (t.description or "").casefold()]; return self.task_list_result(answer=f"Найдено задач: {len(m)}.",tasks=m,filters={"phrase":p})
    async def task_search_assignee(self,args):
        a=args["assignee"].strip(); tasks=await self.a.search_tasks(f"assignee = {a}"); return self.task_list_result(answer=f"У исполнителя {a} найдено задач: {len(tasks)}.",tasks=tasks,filters={"assignee":a})
    async def task_search_status(self,args):
        r=args["status"].strip().casefold(); tasks=await self.a.search_tasks(""); m=[t for t in tasks if r==t.status.value.casefold() or r==t.status_category.value.casefold() or r in t.status.value.casefold()]; return self.task_list_result(answer=f"В статусе «{args['status']}» найдено задач: {len(m)}.",tasks=m,filters={"status":args["status"]})
    async def task_search_sprint(self,args):
        s=args["sprint_id"].upper(); tasks=await self.a.get_sprint_tasks(s); return self.task_list_result(answer=f"В спринте {s} найдено задач: {len(tasks)}.",tasks=tasks,filters={"sprint_id":s},evidence_type="sprint_task")
    async def task_search_release(self,args):
        r=args["release_id"].upper(); tasks=await self.a.get_release_tasks(r); return self.task_list_result(answer=f"В релизе {r} найдено задач: {len(tasks)}.",tasks=tasks,filters={"release_id":r},evidence_type="release_task")
    async def task_search_product(self,args):
        p=args["product"].upper(); tasks=await self.a.search_tasks(f"project = {p}"); return self.task_list_result(answer=f"В продукте {p} найдено задач: {len(tasks)}.",tasks=tasks,filters={"product":p})
    async def task_search_attachments(self,args):
        requested=args.get("attachment_type"); kind=AttachmentType(requested) if requested else None; tasks=await self.a.search_tasks(""); matches=[]; ev=[]
        for t in tasks:
            items=await self.a.get_attachment_metadata(t.key); items=[i for i in items if not kind or i.type==kind]
            if items: matches.append({"task":self.task(t),"attachments":[{"id":i.id,"name":i.name,"type":i.type.value,"size_bytes":i.size_bytes} for i in items]}); ev.extend(Evidence(type="attachment",source="as21",entity_id=t.key,label=i.name,value=i.type.value) for i in items)
        return CapabilityResult(answer=f"Найдено задач с {(kind.value.upper() if kind else 'вложениями')}: {len(matches)}.",data={"attachment_type":kind.value if kind else None,"count":len(matches),"results":matches},evidence=ev)
    async def sprint_health(self,args):
        s=args["sprint_id"].upper(); tasks=await self.a.get_sprint_tasks(s); total=len(tasks); done=sum(t.is_completed for t in tasks); blocked=sum(t.is_blocked for t in tasks); active=sum(t.status_category.value=="active_work" for t in tasks); pct=round(done/total*100,1) if total else 0.0; return CapabilityResult(answer=f"{s}: выполнено {done}/{total} ({pct}%), заблокировано {blocked}.",data={"sprint_id":s,"total":total,"completed":done,"active":active,"blocked":blocked,"completion_percent":pct,"tasks":[self.task(t) for t in tasks]},evidence=[Evidence(type="sprint_task",source="as21",entity_id=t.key,label=t.title,value=t.status.value) for t in tasks])
    async def release_health(self,args):
        r=args["release_id"].upper(); tasks=await self.a.get_release_tasks(r); total=len(tasks); done=sum(t.is_completed for t in tasks); blocked=sum(t.is_blocked for t in tasks); pct=round(done/total*100,1) if total else 0.0; return CapabilityResult(answer=f"{r}: готовность {pct}%, выполнено {done}/{total}, заблокировано {blocked}.",data={"release_id":r,"total":total,"completed":done,"blocked":blocked,"completion_percent":pct,"tasks":[self.task(t) for t in tasks]},evidence=[Evidence(type="release_task",source="as21",entity_id=t.key,label=t.title,value=t.status.value) for t in tasks])
    async def overview(self,args):
        tasks=await self.a.search_tasks(""); total=len(tasks); done=sum(t.is_completed for t in tasks); blocked=sum(t.is_blocked for t in tasks); active=sum(t.status_category.value=="active_work" for t in tasks); unassigned=sum(t.assignee is None for t in tasks); risks=[self.task(t) for t in tasks if t.is_blocked or (t.priority and t.priority.value in ("Critical","Urgent") and not t.is_completed)]; return CapabilityResult(answer=f"В контуре {total} задач: {active} в работе, {done} завершено, {blocked} заблокировано.",data={"tasks_total":total,"active":active,"completed":done,"blocked":blocked,"unassigned":unassigned,"risks":risks,"adapter":"fake-as21"},evidence=[Evidence(type="portfolio_task",source="as21",entity_id=t.key,label=t.title,value=t.status.value) for t in tasks])
class DeterministicRouter:
    TASK_KEY=re.compile(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+\b",re.I); SPRINT_KEY=re.compile(r"\b[A-Z]+-SPRNT-\d+\b",re.I); RELEASE_KEY=re.compile(r"\b[A-Z]+-\d{4}-Q\d+\b",re.I); ASSIGNEE=re.compile(r"(?:исполнитель|исполнителя|на исполнителе)\s+([A-Za-zА-Яа-я0-9._-]+)",re.I); STATUS=re.compile(r"(?:статус|статусе)\s+[«\"]?([^»\"]+?)[»\"]?(?:$|\s+в\s|\s+для\s)",re.I); PRODUCT=re.compile(r"(?:продукт|продукте|пространств(?:о|е))\s+([A-Za-zА-Яа-я0-9_-]+)",re.I)
    def route(self,q):
        l=q.casefold().strip(); tm=self.TASK_KEY.search(q)
        if tm:
            k=tm.group(0); routes=((("суммар","кратко","что нужно сделать","объясни задачу","описание задачи"),"task_summary"),(("качество постанов","оцени постанов","quality"),"task_quality"),(("чего не хватает","что отсутствует","missing requirements"),"task_missing_requirements"),(("критерии прием","критерии приём","acceptance","тестируем"),"task_acceptance_analysis"),(("зависимост","depends","dependency"),"task_dependency_analysis"),(("блокер","блокиров","что мешает","blocked"),"task_blocker_analysis"),(("похож","дубликат","similar","duplicate"),"task_similar"),(("история","переход","lifecycle"),"task_history"),(("сколько в статус","времени в статус","time in status"),"task_time_in_status"))
            for tokens,intent in routes:
                if any(x in l for x in tokens): return intent,{"task_key":k}
        if any(x in l for x in ("старые задачи","залежал","aging","давно не закры")):
            d=re.search(r"(\d+)\s*(?:дн|дней|дня)",l); return "task_aging",{"threshold_days":d.group(1) if d else "7"}
        if "команд" in l and any(x in l for x in ("нагруз","загруз","team workload","workload")): return "team_workload",{}
        if any(x in l for x in ("wip команды","team wip","незавершенка команды")): return "team_wip",{}
        if any(x in l for x in ("блокировки команды","blocked команды","заблокировано у команды")): return "team_blocked",{}
        if any(x in l for x in ("capacity команды","емкость команды","ёмкость команды","утилизация команды")):
            h=re.search(r"(\d+(?:\.\d+)?)\s*(?:ч|час)",l); return "team_capacity",{"capacity_hours":h.group(1) if h else "40"}
        if any(x in l for x in ("бутылоч","bottleneck","узкие места команды")): return "team_bottlenecks",{}
        if any(x in l for x in ("распределение задач команды","team distribution","распределение по команде")): return "team_distribution",{}
        if any(x in l for x in ("вложен","attachment","файл")):
            for tokens,intent,kind in ((("excel","xlsx","xls","эксел"),"task_search_excel",AttachmentType.EXCEL),(("pdf","пдф"),"task_search_pdf",AttachmentType.PDF),(("msg","письм"),"task_search_msg",AttachmentType.MSG)):
                if any(x in l for x in tokens): return intent,{"attachment_type":kind.value}
            return "task_search_attachments",{}
        if m:=self.ASSIGNEE.search(q): return "task_search_assignee",{"assignee":m.group(1)}
        if m:=self.STATUS.search(q): return "task_search_status",{"status":m.group(1).strip()}
        if m:=self.SPRINT_KEY.search(q):
            s=m.group(0)
            if any(x in l for x in ("покажи задачи","задачи спринта","задач в спринте")): return "task_search_sprint",{"sprint_id":s}
            for tokens,intent in ((("velocity","скорост","велосит"),"sprint_velocity"),(("throughput","пропуск","завершен","завершён"),"sprint_throughput"),(("wip","незаверш","в работе"),"sprint_wip"),(("cycle time","cycle-time","цикл"),"sprint_cycle_time"),(("lead time","lead-time","лид тайм"),"sprint_lead_time"),(("predictability","предсказуем"),"sprint_predictability"),(("risk queue","очередь риск","риски спринта","риск"),"sprint_risk_queue"),(("scope","состав"),"sprint_scope")):
                if any(x in l for x in tokens): return intent,{"sprint_id":s}
            return "sprint_health",{"sprint_id":s}
        if m:=self.RELEASE_KEY.search(q):
            r=m.group(0)
            for tokens,intent in ((("progress","прогресс","готовност","completion"),"release_progress"),(("блокер","блокиров","blocked"),"release_blockers"),(("зависимост","dependency","depends"),"release_dependencies"),(("risk queue","очередь риск","риски релиза","риск"),"release_risk_queue"),(("scope","состав","задачи релиза"),"release_scope")):
                if any(x in l for x in tokens): return intent,{"release_id":r}
            if any(x in l for x in ("покажи задачи","задач в релизе")): return "task_search_release",{"release_id":r}
            return "release_health",{"release_id":r}
        if m:=self.PRODUCT.search(q):
            p=m.group(1); return ("sprint_current",{"product":p}) if any(x in l for x in ("текущий спринт","current sprint","активный спринт")) else ("task_search_product",{"product":p})
        if tm:return "task_lookup",{"task_key":tm.group(0)}
        if any(x in l for x in ("обзор","сводк","что происходит","риски")): return "portfolio_overview",{}
        for p in ("найди ","поиск ","search ","найти "):
            if l.startswith(p): return "task_search",{"phrase":q[len(p):].strip().strip('"“”')}
        return "task_search",{"phrase":q.strip()}
class HarnessRuntime:
    def __init__(self,adapter):
        self.adapter=adapter; self.router=DeterministicRouter(); self.capabilities=CapabilityRegistry(); self.skills=SkillRegistry(); d=PortfolioCapabilities(adapter); i=TaskIntelligenceCapabilities(adapter); a=AdvancedTaskCapabilities(adapter); s=SprintIntelligenceCapabilities(adapter); t=TeamIntelligenceCapabilities(adapter); r=ReleaseIntelligenceCapabilities(adapter)
        specs=[("task-lookup","task_lookup","task.lookup",d.task_lookup),("task-search","task_search","task.search",d.task_search),("task-search-attachments","task_search_attachments","task.search_attachments",d.task_search_attachments),("task-search-excel","task_search_excel","task.search_attachment_excel",d.task_search_attachments),("task-search-pdf","task_search_pdf","task.search_attachment_pdf",d.task_search_attachments),("task-search-msg","task_search_msg","task.search_attachment_msg",d.task_search_attachments),("task-search-assignee","task_search_assignee","task.search_assignee",d.task_search_assignee),("task-search-status","task_search_status","task.search_status",d.task_search_status),("task-search-sprint","task_search_sprint","task.search_sprint",d.task_search_sprint),("task-search-release","task_search_release","task.search_release",d.task_search_release),("task-search-product","task_search_product","task.search_product",d.task_search_product),("task-summary","task_summary","task.summary",i.summary),("task-quality","task_quality","task.quality",i.quality_report),("task-missing-requirements","task_missing_requirements","task.missing_requirements",i.missing_requirements),("task-acceptance-analysis","task_acceptance_analysis","task.acceptance_analysis",a.acceptance_analysis),("task-dependency-analysis","task_dependency_analysis","task.dependencies",a.dependencies),("task-blocker-analysis","task_blocker_analysis","task.blockers",a.blockers),("task-similar","task_similar","task.similar",a.similar),("task-history","task_history","task.history",i.history),("task-time-in-status","task_time_in_status","task.time_in_status",i.time_in_status),("task-aging","task_aging","task.aging",i.aging),("sprint-health","sprint_health","sprint.health",d.sprint_health),("sprint-current","sprint_current","sprint.current",s.current),("sprint-scope","sprint_scope","sprint.scope",s.scope),("sprint-velocity","sprint_velocity","sprint.velocity",s.velocity),("sprint-throughput","sprint_throughput","sprint.throughput",s.throughput),("sprint-wip","sprint_wip","sprint.wip",s.wip),("sprint-cycle-time","sprint_cycle_time","sprint.cycle_time",s.cycle_time),("sprint-lead-time","sprint_lead_time","sprint.lead_time",s.lead_time),("sprint-predictability","sprint_predictability","sprint.predictability",s.predictability),("sprint-risk-queue","sprint_risk_queue","sprint.risk_queue",s.risk_queue),("team-workload","team_workload","team.workload",t.workload),("team-wip","team_wip","team.wip",t.wip),("team-blocked","team_blocked","team.blocked",t.blocked),("team-capacity","team_capacity","team.capacity",t.capacity),("team-bottlenecks","team_bottlenecks","team.bottlenecks",t.bottlenecks),("team-distribution","team_distribution","team.distribution",t.distribution),("release-health","release_health","release.health",d.release_health),("release-scope","release_scope","release.scope",r.scope),("release-progress","release_progress","release.progress",r.progress),("release-blockers","release_blockers","release.blockers",r.blockers),("release-dependencies","release_dependencies","release.dependencies",r.dependencies),("release-risk-queue","release_risk_queue","release.risk_queue",r.risk_queue),("portfolio-overview","portfolio_overview","portfolio.overview",d.overview)]
        for sid,intent,cid,h in specs:self.capabilities.register(cid,h);self.skills.register(ExecutableSkill(sid,"1.0.0",intent,cid,f"Executable {intent} skill"))
    async def process(self,request):
        started=time.perf_counter(); trace=str(uuid.uuid4()); session=request.session_id or str(uuid.uuid4()); q=request.query.strip()
        if not q:return HarnessResponse(status=ResponseStatus.FAILED,trace_id=trace,session_id=session,answer="Пустой запрос.",warnings=["query_empty"],latency_ms=(time.perf_counter()-started)*1000)
        try:
            intent,args=self.router.route(q); skill=self.skills.resolve(intent); result=await self.capabilities.execute(skill.capability_id,args); return HarnessResponse(status=ResponseStatus.COMPLETED,trace_id=trace,session_id=session,answer=result.answer,intent=intent,skill_id=skill.id,skill_version=skill.version,data=result.data,evidence=result.evidence,warnings=result.warnings,latency_ms=(time.perf_counter()-started)*1000)
        except Exception:return HarnessResponse(status=ResponseStatus.FAILED,trace_id=trace,session_id=session,answer="Не удалось выполнить запрос.",warnings=["runtime_failure"],latency_ms=(time.perf_counter()-started)*1000)
def build_fake_runtime(): return HarnessRuntime(FakeAS21Adapter())
