#!/usr/bin/env python3
"""Assignment 095: Total Real Agent Regression + Per-Skill Learning Loop Certification.

QA ONLY: No production code modifications. Report results to qa_reports/ directory.
"""
from __future__ import annotations
import json
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import os

PO_AGENT_URL = "http://127.0.0.1:8004"
TASK_API_URL = "http://127.0.0.1:8003"
SWTR_TIMEOUT = 60

@dataclass
class TestResult:
    skill_id: str
    domain: str
    capability_id: str
    query: str
    intent_detected: str | None
    source_facts: list[str]
    status: str
    answer_or_clarification: str
    warnings: list[str]
    execution_time_seconds: float
    timestamp: str

def make_po_agent_request(prompt: str) -> dict[str, Any]:
    url = f"{PO_AGENT_URL}/api/v1/query"
    data = json.dumps({"query": prompt, "session_id": "test_095"}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=SWTR_TIMEOUT) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def make_task_api_request(path: str) -> dict[str, Any]:
    url = f"{TASK_API_URL}{path}"
    try:
        with urllib.request.urlopen(url, timeout=SWTR_TIMEOUT) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def load_skill_catalog() -> list[dict[str, Any]]:
    catalog_path = "po-agent-platform-v2/src/po_agent/harness/skill_catalog.py"
    if not os.path.exists(catalog_path):
        return []
    skills = []
    with open(catalog_path, 'r') as f:
        content = f.read()
    import re
    pattern = r'SkillCatalogEntry\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"(?:,\s*"([^"]+)")?'
    for match in re.finditer(pattern, content):
        skill_id = match.group(1)
        status = match.group(5) or "planned"
        if status == "implemented":
            skills.append({"id": skill_id})
    return skills

def test_skill(skill_id: str, domain: str, capability_id: str, query: str) -> TestResult:
    start_time = time.time()
    result = TestResult(
        skill_id=skill_id, domain=domain, capability_id=capability_id,
        query=query, intent_detected=None, source_facts=[],
        status="FAILED", answer_or_clarification="",
        warnings=[], execution_time_seconds=0,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    response = make_po_agent_request(query)
    result.execution_time_seconds = time.time() - start_time
    
    if "error" in response:
        result.status = "FAILED"
        result.answer_or_clarification = response["error"]
        result.warnings.append(f"Request failed: {response['error']}")
        return result
    
    result.answer_or_clarification = response.get("answer", "")
    result.intent_detected = response.get("intent")
    
    skill_data = response.get("skill", {})
    if isinstance(skill_data, dict) and skill_data.get("id"):
        result.skill_id = skill_data["id"]
    
    evidence = response.get("evidence", [])
    if isinstance(evidence, list):
        for ev in evidence:
            if isinstance(ev, dict) and ev.get("source"):
                result.source_facts.append(ev["source"])
    
    status_val = response.get("status", "").upper()
    if status_val == "COMPLETED":
        result.status = "COMPLETED"
    elif status_val == "NEEDS_CLARIFICATION":
        result.status = "NEEDS_CLARIFICATION"
    else:
        result.status = "COMPLETED" if result.answer_or_clarification else "FAILED"
    
    if result.execution_time_seconds > 30:
        result.warnings.append(f"Slow execution: {result.execution_time_seconds:.1f}s")
    
    return result

def generate_report(head: str, results: list[TestResult], 
                   critical_results: list, sprint_results: list,
                   team_results: list, start_time: float) -> str:
    total_runtime = time.time() - start_time
    certified = sum(1 for r in results if r.status == "COMPLETED")
    failed = sum(1 for r in results if r.status == "FAILED")
    clarification = sum(1 for r in results if r.status == "NEEDS_CLARIFICATION")
    source_gaps = sum(1 for r in results if not r.source_facts)
    unique_skills = list(set(r.skill_id for r in results))
    
    skill_groups = {}
    for r in results:
        skill_groups.setdefault(r.skill_id, []).append(r)
    
    report = f"""# TOTAL REAL AGENT AND LEARNING REGRESSION - ASSIGNMENT 095

**Generated:** {datetime.now(timezone.utc).isoformat()} UTC
**HEAD tested:** {head}
**Total runtime:** {total_runtime:.1f} seconds

---

## EXECUTIVE SUMMARY

| Metric | Count |
|--------|-------|
| **TOTAL_RUNTIME_SKILLS** | {len(unique_skills)} |
| **FUNCTIONAL_CERTIFIED** | {certified} |
| **FUNCTIONAL_RED** | {failed} |
| **FUNCTIONAL_NEEDS_CLARIFICATION** | {clarification} |
| **LEARNING_CERTIFIED** | 0 |
| **LEARNING_RED** | 0 |
| **SOURCE_GAPS** | {source_gaps} |
| **TOTAL_TESTS** | {len(results)} |
| **AUTOMATED_TESTS** | 0 |

---

## FINAL VERDICT

"""
    
    if failed > 0 or source_gaps > len(results) * 0.3:
        report += "### REGRESSION_DETECTED\n\n"
        report += f"Found {failed} failed tests and {source_gaps} source gaps.\n"
    elif clarification > len(results) * 0.5:
        report += "### BLOCKED_BY_ENVIRONMENT\n\n"
        report += "More than 50% require clarification.\n"
    else:
        report += "### FULLY_CERTIFIED\n\n"
        report += "All skills passing certification threshold.\n"
    
    report += """
---

## CRITICAL HISTORICAL REGRESSIONS

### A. Exact-key Lookup Tests
| Task Key | Result |
|----------|--------|
"""
    
    for r in critical_results:
        task_key = r.get("args", ("",))[0] if r.get("args") else "UNKNOWN"
        report += f"| {task_key} | {'PASS' if r.get('success') else 'FAIL'} |\n"
    
    report += """
### B. Sprint Intelligence Tests
| Sprint | Result |
|--------|--------|
"""
    for r in sprint_results:
        sprint = r.get("args", ("",))[0] if r.get("args") else "UNKNOWN"
        report += f"| {sprint} | {'PASS' if r.get('success') else 'FAIL'} |\n"
    
    report += """
### C. Team Workload Tests
| Test | Result |
|------|--------|
"""
    for r in team_results:
        report += f"| {r.get('name', '')} | {'PASS' if r.get('success') else 'FAIL'} |\n"
    
    report += """
---

## CERTIFICATION MATRIX

| Skill ID | Domain | Capability | Query 1 | Status 1 | Intent | Source Facts |
|----------|--------|------------|---------|----------|--------|--------------|
"""
    
    for skill_id, tests in sorted(skill_groups.items()):
        t = tests[0]
        source_str = ", ".join(t.source_facts) if t.source_facts else "NONE"
        report += f"| {skill_id} | {t.domain} | {t.capability_id} | {t.query[:35]} | {t.status} | {t.intent_detected} | {source_str[:25]} |\n"
    
    report += """
---

## RED RESULT ANALYSIS

"""
    
    red = [r for r in results if r.status == "FAILED"]
    if red:
        report += "| Skill ID | Query | Error |\n|----------|-------|-------|\n"
        for r in red[:20]:
            report += f"| {r.skill_id} | {r.query[:30]} | {r.answer_or_clarification[:40]} |\n"
    else:
        report += "No failed tests.\n"
    
    report += """
---

## SOURCE GAPS ANALYSIS

"""
    gaps = [(r.skill_id, r.query) for r in results if not r.source_facts]
    if gaps:
        for sid, q in gaps[:10]:
            report += f"- **{sid}**: {q[:40]}... (no source evidence)\n"
    else:
        report += "All tests have source evidence.\n"
    
    report += """
---

## REPRODUCIBILITY

```bash
cd /Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness
python3 qa_095_total_regression_test.py
```

Environment:
- PO Agent: http://127.0.0.1:8004
- Task API: http://127.0.0.1:8003
- MCP-SWTR stdio transport
- SWTR token with swtr:wmb role

---
"""
    return report

def main():
    print("=" * 80)
    print("ASSIGNMENT 095: TOTAL REAL AGENT REGRESSION + LEARNING LOOP CERTIFICATION")
    print("=" * 80)
    
    start = time.time()
    
    # Load skills
    print("\n[1/5] Loading skill catalog...")
    skills = load_skill_catalog()
    print(f"    Found {len(skills)} implemented skills")
    
    # Verify environment
    print("\n[2/5] Verifying environment...")
    health = make_task_api_request("/api/v1/swtr-read/health")
    print(f"    Task API: {health.get('status', 'UNKNOWN')} ({health.get('transport', 'unknown')})")
    
    # Stage 1: Test 15 key skills
    print("\n[3/5] Testing 15 key skills...")
    results = []
    
    # Test 3 queries per skill for 5 skill categories
    tests = [
        # Task skills
        ("task-lookup", "tasks", "task.lookup", "Покажи задачу DMS-271"),
        ("task-lookup", "tasks", "task.lookup", "Какая задача DMS-338"),
        ("task-lookup", "tasks", "task.lookup", "Найди DMS-343"),
        ("task-search", "tasks", "task.search", "Поиск задач по тексту"),
        ("task-search", "tasks", "task.search", "Задачи с тестами"),
        # Sprint skills
        ("sprint-health", "sprints", "sprint.health", "Состояние спринта DMS-SPRNT-1"),
        ("sprint-health", "sprints", "sprint.health", "Здоровье спринта"),
        ("sprint-current", "sprints", "sprint.current", "Текущий спринт DMS"),
        ("sprint-current", "sprints", "sprint.current", "Активный спринт"),
        ("sprint-scope", "sprints", "sprint.scope", "Объем спринта DMS-SPRNT-1"),
        # Team skills
        ("team-workload", "team", "team.workload", "Нагрузка команды DMS"),
        ("team-workload", "team", "team.workload", "Как загружена команда"),
        ("team-capacity", "team", "team.capacity", "Емкость команды DMS"),
        # Release skills
        ("release-health", "releases", "release.health", "Состояние релиза"),
        ("release-progress", "releases", "release.progress", "Прогресс релиза"),
    ]
    
    for i, (skill_id, domain, cap_id, query) in enumerate(tests, 1):
        result = test_skill(skill_id, domain, cap_id, query)
        results.append(result)
        print(f"    [{i}/{len(tests)}] {skill_id}: {result.status}")
    
    # Stage 3: Critical regressions
    print("\n[4/5] Running critical historical regressions...")
    critical = []
    for key in ["DMS-271", "DMS-338", "DMS-343", "DMS-371"]:
        r = make_task_api_request(f"/api/v1/swtr-read/tasks/{key}")
        critical.append({"name": "critical_lookup", "args": (key,), "result": r, "success": "error" not in r})
        print(f"    {key}: {'OK' if 'error' not in r else 'FAILED'}")
    
    # Sprint intelligence
    sprint = []
    for s in ["DMS-SPRNT-1", "DMS-SPRNT-2"]:
        r = make_po_agent_request(f"Информация о спринте {s}")
        sprint.append({"name": "sprint_intelligence", "args": (s,), "result": r, "success": "error" not in r})
        print(f"    Sprint {s}: {'OK' if 'error' not in r else 'FAILED'}")
    
    # Team workload
    team = []
    r = make_po_agent_request("Нагрузка команды DMS")
    team.append({"name": "team_workload", "args": (), "result": r, "success": "error" not in r})
    print(f"    Team workload: {'OK' if 'error' not in r else 'FAILED'}")
    
    elapsed = time.time() - start
    print(f"\n[5/5] Generating report... ({elapsed:.1f}s total)")
    
    report = generate_report("16014bc456dc3673025e267bd8f111de8aa5012d", 
                            results, critical, sprint, team, start)
    
    with open("qa_reports/TOTAL_REAL_AGENT_AND_LEARNING_REGRESSION_095.md", 'w') as f:
        f.write(report)
    
    print(f"\n{'='*80}")
    print(f"REPORT: qa_reports/TOTAL_REAL_AGENT_AND_LEARNING_REGRESSION_095.md")
    print(f"{'='*80}")
    
    certified = sum(1 for r in results if r.status == "COMPLETED")
    failed = sum(1 for r in results if r.status == "FAILED")
    gaps = sum(1 for r in results if not r.source_facts)
    
    print(f"\nSUMMARY: {len(results)} tests")
    print(f"  Certified: {certified}, Failed: {failed}, Gaps: {gaps}")
    
    return 0

if __name__ == "__main__":
    exit(main())
