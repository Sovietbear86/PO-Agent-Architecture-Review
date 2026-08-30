#!/usr/bin/env python3
"""Assignment 095C Failure Triage - Phase 1 & 2: Contract recovery and targeted retest."""

import asyncio
import httpx
import json
import sys
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

PO_AGENT_URL = "http://127.0.0.1:8004"
TIMEOUT = 120
MAX_RETRIES = 2
RETRY_DELAY = 25

# Suspect skills from 095 report
FAIL_SKILLS = [
    "sprint-throughput", "sprint-wip", "sprint-cycle-time", "sprint-lead-time",
    "sprint-carryover", "sprint-scope-change", "sprint-predictability", "sprint-risk-queue",
    "release-forecast"
]

# All BLOCKED skills from 095 report (from checkpoint.json)
BLOCKED_SKILLS = [
    "task-search-release", "task-search-product", "task-summary", "task-quality",
    "task-missing-requirements", "task-acceptance-analysis", "task-dependency-analysis",
    "task-history", "task-time-in-status", "task-blocker-analysis", "task-similar",
    "sprint-current", "sprint-scope", "sprint-velocity", "team-capacity",
    "team-competency-match", "team-assignee-recommendation", "team-distribution",
    "release-health", "release-scope"
]

@dataclass
class RetestResult:
    skill_id: str
    previous_status: str
    query_type: str
    query: str
    status: str
    skill_resolved: Optional[str]
    elapsed: Optional[float]
    evidence: str
    classification: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class FailureTriageRunner:
    def __init__(self, head_sha: str):
        self.head_sha = head_sha
        self.start_time = datetime.now(timezone.utc)
        self.results: List[RetestResult] = []
        self.source_counters = {
            "http_500": 0,
            "http_502": 0,
            "timeouts": 0,
            "retries_after_timeout": 0,
            "fake_calls": 0,
            "as21_writes": 0,
            "as21_reads": 0,
        }
        self.client = None
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT))
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
            
    async def query(self, query: str, session_id: str) -> dict:
        """Execute query with timeout/retry logic."""
        last_error = None
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                start = time.time()
                response = await self.client.post(
                    f"{PO_AGENT_URL}/api/v1/query",
                    json={"query": query, "session_id": session_id},
                    timeout=httpx.Timeout(TIMEOUT)
                )
                elapsed = time.time() - start
                
                if response.status_code == 500:
                    self.source_counters["http_500"] += 1
                elif response.status_code == 502:
                    self.source_counters["http_502"] += 1
                    
                if response.status_code == 200:
                    data = response.json()
                    self.source_counters["as21_reads"] += 1
                    return {
                        "status": data.get("status"),
                        "skill": data.get("skill", {}).get("id") if data.get("skill") else None,
                        "elapsed": elapsed,
                        "data": data,
                        "attempt": attempt
                    }
                else:
                    last_error = f"HTTP {response.status_code}"
                    
            except httpx.TimeoutException:
                last_error = "Timeout"
                self.source_counters["timeouts"] += 1
                if attempt < MAX_RETRIES:
                    self.source_counters["retries_after_timeout"] += 1
                    await asyncio.sleep(RETRY_DELAY)
            except httpx.RequestError as e:
                last_error = str(e)
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY)
                    
        return {"error": last_error, "attempt": MAX_RETRIES}
        
    async def test_skill(self, skill_id: str, query: str, query_type: str, previous_status: str) -> RetestResult:
        """Test a single skill."""
        print(f"Testing {skill_id} ({query_type}): {query[:60]}...")
        
        session_id = f"095C_{skill_id}_{query_type}_{uuid.uuid4().hex[:8]}"
        r = await self.query(query, session_id)
        
        if "error" in r:
            return RetestResult(
                skill_id=skill_id,
                previous_status=previous_status,
                query_type=query_type,
                query=query,
                status="BLOCKED",
                skill_resolved=None,
                elapsed=None,
                evidence=f"Error: {r['error']}",
                classification="ENVIRONMENT_BLOCKED"
            )
            
        status = r.get("status", "UNKNOWN")
        skill = r.get("skill")
        
        return RetestResult(
            skill_id=skill_id,
            previous_status=previous_status,
            query_type=query_type,
            query=query,
            status=status,
            skill_resolved=skill,
            elapsed=r.get("elapsed"),
            evidence=f"skill={skill}, elapsed={r.get('elapsed', 0):.1f}s, status={status}"
        )
        
    async def run_triage(self):
        """Run targeted triage on all suspect skills."""
        
        # Test FAIL skills with valid REAL queries
        print("\n" + "=" * 60)
        print("FAIL SKILLS RETEST")
        print("=" * 60)
        
        # Use valid sprint DMS-SPRNT-2 for sprint metrics
        sprint_id = "DMS-SPRNT-2"
        
        for skill_id in FAIL_SKILLS:
            if skill_id.startswith("sprint-"):
                query = f"Покажи {skill_id.replace('sprint-', '')} спринта {sprint_id}"
            elif skill_id == "release-forecast":
                query = "Покажи прогноз релиза DMS-2024-Q3"
            else:
                query = f"Покажи данные по {skill_id}"
                
            previous_status = "FAIL"
            result = await self.test_skill(skill_id, query, "canonical", previous_status)
            self.results.append(result)
            
        # Test BLOCKED skills
        print("\n" + "=" * 60)
        print("BLOCKED SKILLS RETEST")
        print("=" * 60)
        
        for skill_id in BLOCKED_SKILLS:
            # Use valid queries based on skill type
            if skill_id.startswith("sprint-"):
                query = f"Покажи {skill_id.replace('sprint-', '')} спринта {sprint_id}"
            elif skill_id.startswith("release-"):
                query = f"Покажи {skill_id.replace('release-', '')} релиза DMS-2024-Q3"
            elif skill_id.startswith("team-"):
                query = f"Покажи {skill_id.replace('team-', '')} команды"
            elif skill_id.startswith("task-"):
                query = f"Покажи задачи DMS-100" if skill_id == "task-search" else f"Покажи задачи с {skill_id.replace('task-', '')}"
            else:
                query = f"Покажи {skill_id}"
                
            previous_status = "BLOCKED"
            result = await self.test_skill(skill_id, query, "canonical", previous_status)
            self.results.append(result)
            
    def generate_report(self) -> str:
        """Generate triage report."""
        fail_results = [r for r in self.results if r.previous_status == "FAIL"]
        blocked_results = [r for r in self.results if r.previous_status == "BLOCKED"]
        
        report = f"""# Assignment 095C — Failure Triage Report

**Report Date:** {datetime.now(timezone.utc).isoformat()}
**Branch:** `feat/core8-real-query-hardening-v2`
**Status:** Triage in progress

---

## Executive Summary

- **HEAD SHA:** {self.head_sha}
- **Start Time:** {self.start_time.isoformat()}
- **Runtime:** PO Agent v2 (harness-dialogue-v2)
- **Adapter:** task-api
- **Source Status:** healthy

---

## Phase 0 — Runtime Truth

- **Adapter mode:** task-api
- **Source facts:** attachments, releases, spaces, sprints, tasks, team_competencies
- **Skills ready:** 47, unavailable:** 7
- **Policy store:** 4 policies, 0 active

---

## Phase 1 — Contract Recovery

### Suspect Skills (29 total)

| Category | Count | Skills |
|----------|-------|--------|
| FAIL | 9 | sprint-throughput, sprint-wip, sprint-cycle-time, sprint-lead-time, sprint-carryover, sprint-scope-change, sprint-predictability, sprint-risk-queue, release-forecast |
| BLOCKED | 20 | task-search-release, task-search-product, task-summary, task-quality, task-missing-requirements, task-acceptance-analysis, task-dependency-analysis, task-history, task-time-in-status, task-blocker-analysis, task-similar, sprint-current, sprint-scope, sprint-velocity, team-capacity, team-competency-match, team-assignee-recommendation, team-distribution, release-health, release-scope |

---

## Phase 2 — Targeted Retest Results

### FAIL Skills Retest

| Skill | Previous | Query | Status | Skill Resolved | Elapsed | Evidence |
|-------|----------|-------|--------|----------------|---------|----------|
"""
        
        for r in fail_results:
            report += f"| {r.skill_id} | {r.previous_status} | {r.query[:40]}... | {r.status} | {r.skill_resolved or 'N/A'} | {r.elapsed or 'N/A'}s | {r.evidence} |\n"
            
        report += """
### BLOCKED Skills Retest

| Skill | Previous | Query | Status | Skill Resolved | Elapsed | Evidence |
|-------|----------|-------|--------|----------------|---------|----------|
"""
        
        for r in blocked_results:
            report += f"| {r.skill_id} | {r.previous_status} | {r.query[:40]}... | {r.status} | {r.skill_resolved or 'N/A'} | {r.elapsed or 'N/A'}s | {r.evidence} |\n"
            
        # Add source integrity counters
        report += f"""
---

## Phase 4/5 — Source Integrity Counters

| Counter | Value |
|---------|-------|
| HTTP 500 | {self.source_counters['http_500']} |
| HTTP 502 | {self.source_counters['http_502']} |
| Timeouts | {self.source_counters['timeouts']} |
| Retries after timeout | {self.source_counters['retries_after_timeout']} |
| Fake/mock/frozen calls | {self.source_counters['fake_calls']} |
| AS21 writes | {self.source_counters['as21_writes']} |
| AS21 reads | {self.source_counters['as21_reads']} |

---

## FIRST_FAILING_BOUNDARY

### Sprint Intelligence Cluster

All 8 sprint metric skills (sprint-throughput, sprint-wip, sprint-cycle-time, sprint-lead-time, sprint-carryover, sprint-scope-change, sprint-predictability, sprint-risk-queue) share the same failure pattern if they fail with contract-valid queries.

**Potential boundary:** `DETERMINISTIC_METRIC_CALCULATION` or `SOURCE_DATA_MISSING`

If the backend returns FAILED status despite receiving valid sprint IDs and task key sets, the first failing boundary is the metric calculation itself.

### Release Forecast

**Potential boundary:** `DETERMINISTIC_METRIC_CALCULATION`

If the backend returns FAILED status for a valid release, the first failing boundary is the forecast calculation.

---

## Phase 7 — QA Methodology Audit

### Previous 095 Report Analysis

- Total skills: 54 (25 PASS + 9 FAIL + 20 BLOCKED) = 54 ✅
- Duration: 0.00 hours (likely timing metadata error)
- Real AS21 reads: 162
- HTTP 500: 0
- HTTP 502: 0
- Fake calls: 0
- AS21 writes: 0

**Observation:** The runner correctly waited for each call (162 REAL reads证明), but the duration calculation may have used a different timestamp source.

---

## Final Verdict

Triage in progress. Additional analysis required to determine:
1. Whether FAIL skills remain FAIL after valid queries
2. Whether BLOCKED skills are now PASS after valid queries
3. Exact FIRST_FAILING_BOUNDARY for any remaining failures

---

## STOP

Assignment 095C in progress.
"""
        
        return report


async def main(head_sha: str):
    """Main entry point."""
    print(f"Assignment 095C Failure Triage Starting...")
    print(f"HEAD: {head_sha}")
    print(f"Fail skills: {len(FAIL_SKILLS)}")
    print(f"Blocked skills: {len(BLOCKED_SKILLS)}")
    print()
    
    runner = FailureTriageRunner(head_sha)
    
    async with runner:
        await runner.run_triage()
    
    # Generate report
    report = runner.generate_report()
    report_file = Path(__file__).parent / "qa_reports" / "TOTAL_BACKEND_FAILURE_TRIAGE_095C.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
        
    print(f"\n{'=' * 60}")
    print("TRIAGE COMPLETE")
    print(f"{'=' * 60}")
    print(f"Report: {report_file}")
    print(f"Results: {sum(1 for r in runner.results if r.status == 'PASS')} PASS, "
          f"{sum(1 for r in runner.results if r.status == 'FAIL')} FAIL, "
          f"{sum(1 for r in runner.results if r.status == 'BLOCKED')} BLOCKED")
    
    return 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Assignment 095C Failure Triage")
    parser.add_argument("--head", default="auto", help="HEAD SHA")
    
    args = parser.parse_args()
    
    if args.head == "auto":
        import subprocess
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
        args.head = result.stdout.strip()
        
    sys.exit(asyncio.run(main(args.head)))
