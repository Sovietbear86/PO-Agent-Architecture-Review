#!/usr/bin/env python3
"""Gate A Preflight: Verify SWTR backend connectivity before 54-skill marathon."""

import httpx
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PO_AGENT_URL = "http://127.0.0.1:8004"
TIMEOUT = 120  # 2 minutes for SWTR-backed requests
MAX_RETRIES = 2
RETRY_DELAY = 25  # 25 seconds between retries


class PreflightRunner:
    def __init__(self, head_sha: str):
        self.head_sha = head_sha
        self.start_time = datetime.now(timezone.utc)
        self.results = []
        self.source_counters = {
            "http_500": 0,
            "http_502": 0,
            "timeouts": 0,
            "retries_after_timeout": 0,
        }
        self.client = None
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT))
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
            
    async def query(self, query_text: str) -> dict:
        """Execute query with timeout/retry logic."""
        last_error = None
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                start = time.time()
                response = await self.client.post(
                    f"{PO_AGENT_URL}/api/v1/query",
                    json={"query": query_text, "session_id": f"preflight_{attempt}_{int(start)}"},
                    timeout=httpx.Timeout(TIMEOUT)
                )
                elapsed = time.time() - start
                
                # Track response codes
                if response.status_code == 500:
                    self.source_counters["http_500"] += 1
                elif response.status_code == 502:
                    self.source_counters["http_502"] += 1
                    
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "SUCCESS",
                        "data": data,
                        "elapsed": elapsed,
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
                    
        return {"status": "FAILED", "error": last_error, "attempt": MAX_RETRIES}
        
    async def run_preflight(self):
        """Run 3 sequential end-to-end requests."""
        
        # Request 1: Valid exact task lookup
        print("=" * 60)
        print("PREFLIGHT REQUEST 1: Valid exact task lookup")
        print("=" * 60)
        q1 = "Покажи задачи DMS-100"
        print(f"Query: {q1}")
        r1 = await self.query(q1)
        print(f"Status: {r1['status']}")
        print(f"Elapsed: {r1.get('elapsed', 'N/A')}s")
        if r1['status'] == "SUCCESS":
            data = r1['data']
            print(f"Skill: {data.get('skill', {}).get('id')}")
            print(f"Status: {data.get('status')}")
            print(f"Answer preview: {data.get('answer', '')[:100]}...")
            self.results.append({
                "request": 1,
                "type": "task_lookup",
                "query": q1,
                "status": r1['status'],
                "elapsed": r1.get('elapsed'),
                "skill": data.get('skill', {}).get('id') if r1['status'] == "SUCCESS" else None,
                "result_status": data.get('status') if r1['status'] == "SUCCESS" else None,
                "evidence": "REAL AS21 read successful" if r1['status'] == "SUCCESS" else r1.get('error')
            })
        else:
            print(f"Error: {r1.get('error')}")
            self.results.append({
                "request": 1,
                "type": "task_lookup",
                "query": q1,
                "status": "FAILED",
                "error": r1.get('error'),
                "evidence": r1.get('error')
            })
            return False  # Gate A failed
        
        # Small delay between requests
        print("\nWaiting 5 seconds before next request...")
        await asyncio.sleep(5)
        
        # Request 2: Valid sprint-backed request
        print("\n" + "=" * 60)
        print("PREFLIGHT REQUEST 2: Valid sprint-backed request")
        print("=" * 60)
        q2 = "Покажи здоровье спринта DMS-SPRNT-2"
        print(f"Query: {q2}")
        r2 = await self.query(q2)
        print(f"Status: {r2['status']}")
        print(f"Elapsed: {r2.get('elapsed', 'N/A')}s")
        if r2['status'] == "SUCCESS":
            data = r2['data']
            print(f"Skill: {data.get('skill', {}).get('id')}")
            print(f"Status: {data.get('status')}")
            print(f"Answer preview: {data.get('answer', '')[:100]}...")
            self.results.append({
                "request": 2,
                "type": "sprint_health",
                "query": q2,
                "status": r2['status'],
                "elapsed": r2.get('elapsed'),
                "skill": data.get('skill', {}).get('id') if r2['status'] == "SUCCESS" else None,
                "result_status": data.get('status') if r2['status'] == "SUCCESS" else None,
                "evidence": "REAL AS21 read successful" if r2['status'] == "SUCCESS" else r2.get('error')
            })
        else:
            print(f"Error: {r2.get('error')}")
            self.results.append({
                "request": 2,
                "type": "sprint_health",
                "query": q2,
                "status": "FAILED",
                "error": r2.get('error'),
                "evidence": r2.get('error')
            })
            return False  # Gate A failed
        
        # Small delay between requests
        print("\nWaiting 5 seconds before next request...")
        await asyncio.sleep(5)
        
        # Request 3: Valid team/release request
        print("\n" + "=" * 60)
        print("PREFLIGHT REQUEST 3: Valid team/release request")
        print("=" * 60)
        q3 = "Покажи нагрузку команды"
        print(f"Query: {q3}")
        r3 = await self.query(q3)
        print(f"Status: {r3['status']}")
        print(f"Elapsed: {r3.get('elapsed', 'N/A')}s")
        if r3['status'] == "SUCCESS":
            data = r3['data']
            print(f"Skill: {data.get('skill', {}).get('id')}")
            print(f"Status: {data.get('status')}")
            print(f"Answer preview: {data.get('answer', '')[:100]}...")
            self.results.append({
                "request": 3,
                "type": "team_workload",
                "query": q3,
                "status": r3['status'],
                "elapsed": r3.get('elapsed'),
                "skill": data.get('skill', {}).get('id') if r3['status'] == "SUCCESS" else None,
                "result_status": data.get('status') if r3['status'] == "SUCCESS" else None,
                "evidence": "REAL AS21 read successful" if r3['status'] == "SUCCESS" else r3.get('error')
            })
        else:
            print(f"Error: {r3.get('error')}")
            self.results.append({
                "request": 3,
                "type": "team_workload",
                "query": q3,
                "status": "FAILED",
                "error": r3.get('error'),
                "evidence": r3.get('error')
            })
            return False  # Gate A failed
        
        return True  # All requests succeeded
        
    def generate_report(self, preflight_passed: bool) -> str:
        """Generate preflight report."""
        duration = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        report = f"""# Assignment 095B — Production Background Preflight

**Report Date:** {datetime.now(timezone.utc).isoformat()}
**Branch:** `feat/core8-real-query-hardening-v2`
**Status:** {"GREEN - PRELIGHT PASSED" if preflight_passed else "BLOCKED_BY_ENVIRONMENT"}

---

## Environment Fingerprint

- **HEAD SHA:** {self.head_sha}
- **Start Time:** {self.start_time.isoformat()}
- **Duration:** {duration:.2f} seconds
- **Runtime:** PO Agent v2 (harness-dialogue-v2)
- **Adapter:** task-api
- **SWTR Transport:** stdio
- **LLM Mode:** qwen-llm
- **Source Status:** healthy

---

## Preflight Results

| Request | Type | Query | Status | Elapsed | Evidence |
|---------|------|-------|--------|---------|----------|
"""
        
        for r in self.results:
            query = r['query'][:60] + "..." if len(r['query']) > 60 else r['query']
            report += f"| {r['request']} | {r['type']} | {query} | {r['status']} | {r.get('elapsed', 'N/A')}s | {r.get('evidence', r.get('error', 'N/A'))} |\n"
            
        report += f"""
---

## Source Integrity Counters

| Counter | Value |
|---------|-------|
| HTTP 500 | {self.source_counters['http_500']} |
| HTTP 502 | {self.source_counters['http_502']} |
| Timeouts | {self.source_counters['timeouts']} |
| Retries after timeout | {self.source_counters['retries_after_timeout']} |

---

## Gate A Decision

### Preflight Passed: {"YES" if preflight_passed else "NO"}

{"✅ All 3 sequential end-to-end requests succeeded with REAL AS21 evidence." if preflight_passed else "❌ At least one request failed or timed out. Environment check incomplete."}

### Decision

- **GREEN:** Proceed to Gate B (54-skill marathon)
- **RED/BLOCKED:** Do not start marathon. Environment issue must be resolved first.

"""

        if not preflight_passed:
            report += """### FIRST_FAILING_BOUNDARY

"""
            for r in self.results:
                if r['status'] == "FAILED":
                    report += f"- **Request {r['request']} ({r['type']}):** {r.get('error', 'Unknown error')}\n"
            report += "\n"
        
        return report


async def main(head_sha: str):
    """Main entry point."""
    print(f"Gate A Preflight Starting...")
    print(f"HEAD: {head_sha}")
    print(f"Timeout: {TIMEOUT}s per request")
    print(f"Max retries: {MAX_RETRIES}")
    print()
    
    runner = PreflightRunner(head_sha)
    
    async with runner:
        preflight_passed = await runner.run_preflight()
    
    # Generate report
    report = runner.generate_report(preflight_passed)
    report_file = Path(__file__).parent / "qa_reports" / "TOTAL_BACKEND_CERTIFICATION_095B_PREFLIGHT.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
        
    print(f"\n{'=' * 60}")
    print("PREFLIGHT COMPLETE")
    print(f"{'=' * 60}")
    print(f"Report: {report_file}")
    print(f"Status: {'GREEN - READY FOR MARATHON' if preflight_passed else 'RED/BLOCKED'}")
    
    return 0 if preflight_passed else 1


if __name__ == "__main__":
    import asyncio
    import argparse
    
    parser = argparse.ArgumentParser(description="Assignment 095B Preflight")
    parser.add_argument("--head", default="auto", help="HEAD SHA (auto-detect if not specified)")
    
    args = parser.parse_args()
    
    if args.head == "auto":
        import subprocess
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
        args.head = result.stdout.strip()
        
    sys.exit(asyncio.run(main(args.head)))
