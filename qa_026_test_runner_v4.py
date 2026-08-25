#!/usr/bin/env python3
"""QA 026 v4 Targeted Retest Runner.

Targets 19 PRODUCT_FAIL cases from QA 026 v3 with production commit 44c0bb1.

DO NOT modify production code, prompts, capabilities, tests, config, or acceptance.
QA/tester role only.
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# QA Runner Configuration
QA_RUNNER_CONFIG = {
    "MAX_CONCURRENCY": 1,  # Sequential execution only
    "COOLDOWN_BETWEEN_QUERIES_MS": 500,  # 0.5s cooldown between production queries
    "TIMEOUT_PER_QUERY_MS": 60000,  # 60s timeout per query
    "MAX_RETRIES": 3,
}

# Production test cases - 19 PRODUCT_FAILs from QA 026 v3
PRODUCT_FAIL_CASES = {
    "PERSON_CLUSTER": [
        {"id": "D1", "query": "person + sprint: Покажи задачи Моисеева в DMS-SPRNT-2", "expected_filters": {"person_raw": "Моисеева", "sprint_raw": "DMS-SPRNT-2"}},
        {"id": "D2", "query": "person + product: Покажи задачи Моисеева в DMS", "expected_filters": {"person_raw": "Моисеева", "product": "DMS"}},
        {"id": "D3", "query": "person + status: Покажи задачи Моисеева со статусом OPEN", "expected_filters": {"person_raw": "Моисеева", "status_raw": "OPEN"}},
        {"id": "D4", "query": "person + product + status: Покажи задачи Моисеева в DMS со статусом OPEN", "expected_filters": {"person_raw": "Моисеева", "product": "DMS", "status_raw": "OPEN"}},
        {"id": "D5", "query": "person + product + sprint: Покажи задачи Моисеева в DMS-SPRNT-2", "expected_filters": {"person_raw": "Моисеева", "product": "DMS", "sprint_raw": "DMS-SPRNT-2"}},
        {"id": "D6", "query": "person + product + sprint + status: Покажи задачи Моисеева в DMS-SPRNT-2 со статусом OPEN", "expected_filters": {"person_raw": "Моисеева", "product": "DMS", "sprint_raw": "DMS-SPRNT-2", "status_raw": "OPEN"}},
        {"id": "I1", "query": "Покажи задачи Гаранина", "expected_filters": {"person_raw": "Гаранина"}},
        {"id": "I6", "query": "Покажи задачи Гаранина в DMS-SPRNT-1", "expected_filters": {"person_raw": "Гаранина", "sprint_raw": "DMS-SPRNT-1"}},
        {"id": "J1", "query": "Покажи задачи Гаранина", "expected_filters": {"person_raw": "Гаранина"}},
        {"id": "G1", "query": "Покажи задачи Гаранина в DMS-SPRNT-1", "expected_filters": {"person_raw": "Гаранина", "sprint_raw": "DMS-SPRNT-1"}},
        {"id": "G2", "query": "Покажи задачи Гаранна в DMS-SPRNT-1", "expected_filters": {"person_raw": "Гаранна", "sprint_raw": "DMS-SPRNT-1"}},
        {"id": "G4", "query": "Покажи задачи Гаранина в DMS-SPRNT-1", "expected_filters": {"person_raw": "Гаранина", "sprint_raw": "DMS-SPRNT-1"}},
    ],
    "STATUS_CLUSTER": [
        {"id": "I3", "query": "Покажи задачи со статусом todo", "expected_filters": {"status_raw": "todo"}},
        {"id": "I4", "query": "Покажи задачи со статусом in_progress", "expected_filters": {"status_raw": "in_progress"}},
        {"id": "I5", "query": "Покажи задачи со статусом done", "expected_filters": {"status_raw": "done"}},
        {"id": "J5", "query": "Покажи задачи со статусом done", "expected_filters": {"status_raw": "done"}},
    ],
    "PRODUCT_CLUSTER": [
        {"id": "I2", "query": "Покажи задачи в DMS", "expected_filters": {"product": "DMS"}},
        {"id": "J2", "query": "Покажи задачи в DMS", "expected_filters": {"product": "DMS"}},
        {"id": "B1", "query": "Покажи задачи Гаранина в DMS-SPRNT-1", "expected_filters": {"person_raw": "Гаранина", "sprint_raw": "DMS-SPRNT-1"}},
    ],
}

# Regression sample - previously PASS cases
REGRESSION_CASES = {
    "SECTION_B_PASS": [
        {"id": "B2", "query": "Что висит на Гаранине в спринте DMS-SPRNT-1?", "expected_filters": {"person_raw": "Гаранине", "sprint_raw": "DMS-SPRNT-1"}},
        {"id": "B3", "query": "Какие тикеты у Гаранина относятся к DMS-SPRNT-1?", "expected_filters": {"person_raw": "Гаранина", "sprint_raw": "DMS-SPRNT-1"}},
        {"id": "B4", "query": "Выведи работу Родиона Гаранина за DMS-SPRNT-1", "expected_filters": {"person_raw": "Родиона Гаранина", "sprint_raw": "DMS-SPRNT-1"}},
        {"id": "B5", "query": "По DMS-SPRNT-1 что назначено Гаранину?", "expected_filters": {"person_raw": "Гаранину", "sprint_raw": "DMS-SPRNT-1"}},
        {"id": "B6", "query": "Мне нужен список задач пользователя Гаранин в DMS-SPRNT-1", "expected_filters": {"person_raw": "Гаранин", "sprint_raw": "DMS-SPRNT-1"}},
        {"id": "B7", "query": "Покажи, пожалуйста, задачи по DMS-SPRNT-1, которые сейчас на Гаранине", "expected_filters": {"person_raw": "Гаранине", "sprint_raw": "DMS-SPRNT-1"}},
        {"id": "B8", "query": "DMS-SPRNT-1: что у Гаранина?", "expected_filters": {"person_raw": "Гаранина", "sprint_raw": "DMS-SPRNT-1"}},
    ],
    "SECTION_C_PASS": [
        {"id": "C1", "query": "Покажи задачи пользователя Моисеева в пространстве DMS со статусом OPEN", "expected_filters": {"person_raw": "Моисеева", "product": "DMS", "status_raw": "OPEN"}},
        {"id": "C2", "query": "Найди OPEN-задачи Моисеева по DMS", "expected_filters": {"person_raw": "Моисеева", "product": "DMS", "status_raw": "OPEN"}},
        {"id": "C3", "query": "Что в DMS сейчас висит на Моисееве со статусом OPEN?", "expected_filters": {"person_raw": "Моисеева", "product": "DMS", "status_raw": "OPEN"}},
        {"id": "C4", "query": "По пространству DMS покажи работу Моисеева, статус OPEN", "expected_filters": {"person_raw": "Моисеева", "product": "DMS", "status_raw": "OPEN"}},
        {"id": "C5", "query": "У Моисеева какие задачи в DMS имеют статус OPEN?", "expected_filters": {"person_raw": "Моисеева", "product": "DMS", "status_raw": "OPEN"}},
    ],
}

# Source oracle checks
SOURCE_ORACLE_CASES = {
    "ORACLE_SPRINT1": {"id": "OA1", "query": "Oracle: ДМС-СПРНТ-1 содержит задачи?", "expected": "contains_tasks"},
    "ORACLE_SPRINT2": {"id": "OA2", "query": "Oracle: ДМС-СПРНТ-2 содержит задачи?", "expected": "contains_tasks"},
}


class QA026V4TestRunner:
    def __init__(self, po_agent_url: str = "http://localhost:8004"):
        self.po_agent_url = po_agent_url
        self.client = None
        self.results: Dict[str, Any] = {}

    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=self.po_agent_url, timeout=120.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    def _get_session_id(self, query_id: str) -> str:
        """Generate unique session_id per case."""
        return f"qa026v4-{query_id}"

    async def query(self, query: str, session_id: str = "qa026v4", query_id: str = "") -> Dict:
        """Query PO Agent with timing."""
        start_ts = time.perf_counter()
        try:
            r = await self.client.post('/api/v1/query', json={
                'query': query,
                'session_id': session_id
            })
            elapsed_ms = int((time.perf_counter() - start_ts) * 1000)
            
            data = r.json()
            return {
                "query": query,
                "query_id": query_id,
                "status_code": r.status_code,
                "response": data,
                "TOTAL_MS": elapsed_ms,
                "START_TS": start_ts,
                "SESSION_ID": session_id,
                "STATUS": "PASS" if r.status_code == 200 else "FAIL",
                "TIMEOUT": "NO" if elapsed_ms < 60000 else "YES"
            }
        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_ts) * 1000)
            return {
                "query": query,
                "query_id": query_id,
                "status_code": None,
                "error": str(e),
                "TOTAL_MS": elapsed_ms,
                "START_TS": start_ts,
                "SESSION_ID": session_id,
                "STATUS": "ERROR",
                "TIMEOUT": "NO"
            }

    def _extract_semantic_frame(self, result: Dict) -> Dict:
        """Extract semantic frame from response."""
        data = result.get("response", {})
        if not data:
            return {}
        
        # Try to get the semantic frame from response
        # The frame should contain intent_hint, slots, clarifications
        return {
            "intent_hint": data.get("intent"),
            "slots": data.get("data", {}).get("slots", {}),
            "clarifications": data.get("clarifications", []),
            "skill": data.get("skill"),
            "answer": data.get("answer", ""),
            "data": data.get("data", {})
        }

    def _extract_task_keys(self, result: Dict) -> List[str]:
        """Extract task keys from response."""
        data = result.get("response", {})
        if not data:
            return []
        
        # Try structured task list
        tasks = data.get("data", {}).get("data", {}).get("tasks", [])
        if not tasks:
            tasks = data.get("data", {}).get("tasks", [])
        
        keys = []
        for task in tasks:
            if isinstance(task, dict):
                key = task.get("key") or task.get("id") or task.get("source_id")
                if key:
                    keys.append(key)
        
        # Try evidence
        if not keys:
            evidence = data.get("data", {}).get("evidence", [])
            for e in evidence:
                if isinstance(e, dict):
                    eid = e.get("entity_id")
                    if eid:
                        keys.append(eid)
        
        return keys

    async def run_targeted_retest(self) -> Dict:
        """Run targeted retest for 19 PRODUCT_FAIL cases."""
        print("=" * 70)
        print("QA 026 v4 Targeted Retest")
        print("=" * 70)
        print(f"Production commit: 44c0bb1")
        print()

        self.results = {
            "timestamp": datetime.now().isoformat(),
            "product_fail_cases": {},
            "regression_cases": {},
            "source_oracle": {},
            "summary": {}
        }

        # Run PRODUCT_FAIL cases
        for cluster, cases in PRODUCT_FAIL_CASES.items():
            print(f"\n=== {cluster} ({len(cases)} cases) ===")
            for case in cases:
                query_id = case["id"]
                query = case["query"]
                expected = case["expected_filters"]
                
                print(f"\n{query_id}: {query[:60]}...")
                
                session_id = self._get_session_id(query_id)
                result = await self.query(query, session_id=session_id, query_id=query_id)
                
                semantic_frame = self._extract_semantic_frame(result)
                task_keys = self._extract_task_keys(result)
                
                # Determine PASS/FAIL
                status = "PASS"
                if result.get("STATUS") != "PASS":
                    status = "FAIL (HTTP)"
                elif len(task_keys) == 0:
                    status = "FAIL (no tasks)"
                
                print(f"  Status: {status}")
                print(f"  Skill: {semantic_frame.get('skill')}")
                print(f"  Intent: {semantic_frame.get('intent_hint')}")
                print(f"  Slots: {json.dumps(semantic_frame.get('slots', {}), ensure_ascii=False)}")
                print(f"  Task keys: {len(task_keys)}")
                
                self.results["product_fail_cases"][query_id] = {
                    "query": query,
                    "expected_filters": expected,
                    "actual_semantic_frame": semantic_frame,
                    "selected_skill": semantic_frame.get("skill"),
                    "result": {
                        "status_code": result.get("status_code"),
                        "task_keys": task_keys,
                        "TOTAL_MS": result.get("TOTAL_MS"),
                        "STATUS": result.get("STATUS"),
                        "TIMEOUT": result.get("TIMEOUT")
                    },
                    "PASS": status == "PASS"
                }

        # Run regression sample
        print("\n=== REGRESSION SAMPLE ===")
        for cluster, cases in REGRESSION_CASES.items():
            print(f"\n{cluster} ({len(cases)} cases):")
            for case in cases:
                query_id = case["id"]
                query = case["query"]
                expected = case["expected_filters"]
                
                print(f"\n{query_id}: {query[:60]}...")
                
                session_id = self._get_session_id(query_id)
                result = await self.query(query, session_id=session_id, query_id=query_id)
                
                semantic_frame = self._extract_semantic_frame(result)
                task_keys = self._extract_task_keys(result)
                
                status = "PASS"
                if result.get("STATUS") != "PASS":
                    status = "FAIL (HTTP)"
                elif len(task_keys) == 0:
                    status = "FAIL (no tasks)"
                
                print(f"  Status: {status}")
                print(f"  Skill: {semantic_frame.get('skill')}")
                print(f"  Slots: {json.dumps(semantic_frame.get('slots', {}), ensure_ascii=False)}")
                print(f"  Task keys: {len(task_keys)}")
                
                self.results["regression_cases"][query_id] = {
                    "query": query,
                    "expected_filters": expected,
                    "actual_semantic_frame": semantic_frame,
                    "selected_skill": semantic_frame.get("skill"),
                    "result": {
                        "status_code": result.get("status_code"),
                        "task_keys": task_keys,
                        "TOTAL_MS": result.get("TOTAL_MS"),
                        "STATUS": result.get("STATUS"),
                        "TIMEOUT": result.get("TIMEOUT")
                    },
                    "PASS": status == "PASS"
                }

        # Run source oracle checks
        print("\n=== SOURCE ORACLE CHECKS ===")
        for case_id, case in SOURCE_ORACLE_CASES.items():
            query_id = case["id"]
            query = case["query"]
            
            print(f"\n{query_id}: {query}")
            
            session_id = self._get_session_id(query_id)
            result = await self.query(query, session_id=session_id, query_id=query_id)
            
            task_keys = self._extract_task_keys(result)
            
            expected = case["expected"]
            status = "PASS" if expected == "contains_tasks" and len(task_keys) > 0 else "FAIL"
            
            print(f"  Status: {status}")
            print(f"  Task keys: {len(task_keys)}")
            
            self.results["source_oracle"][query_id] = {
                "query": query,
                "expected": expected,
                "actual_task_keys": task_keys,
                "PASS": status == "PASS"
            }

        # Generate summary
        self._generate_summary()
        
        return self.results

    def _generate_summary(self):
        """Generate summary metrics."""
        product_fail = self.results.get("product_fail_cases", {})
        regression = self.results.get("regression_cases", {})
        source_oracle = self.results.get("source_oracle", {})
        
        # Count passes by cluster
        person_pass = sum(1 for k, v in product_fail.items() 
                         if k.startswith(("D1", "D2", "D3", "D4", "D5", "D6", "I1", "I6", "J1", "G1", "G2", "G4")) and v.get("PASS"))
        
        status_pass = sum(1 for k, v in product_fail.items() 
                         if k.startswith(("I3", "I4", "I5", "J5")) and v.get("PASS"))
        
        product_pass = sum(1 for k, v in product_fail.items() 
                          if k.startswith(("I2", "J2", "B1")) and v.get("PASS"))
        
        total_recovered = person_pass + status_pass + product_pass
        total_failures = len(product_fail)
        
        # Count regressions
        new_regressions = sum(1 for k, v in regression.items() if not v.get("PASS"))
        
        # Source oracle
        source_oracle_pass = all(v.get("PASS") for v in source_oracle.values())
        
        self.results["summary"] = {
            "person_cluster": {
                "pass": person_pass,
                "total": 12,
                "pass_rate": f"{person_pass}/12"
            },
            "status_cluster": {
                "pass": status_pass,
                "total": 4,
                "pass_rate": f"{status_pass}/4"
            },
            "product_cluster": {
                "pass": product_pass,
                "total": 3,
                "pass_rate": f"{product_pass}/3"
            },
            "total_recovered": {
                "count": total_recovered,
                "total": 19,
                "rate": f"{total_recovered}/19"
            },
            "new_regressions": new_regressions,
            "source_oracle": "PASS" if source_oracle_pass else "FAIL",
            "ready_for_full_qa026": "YES" if total_recovered >= 17 and new_regressions == 0 and source_oracle_pass else "NO"
        }

    def print_summary(self, results: Dict):
        """Print summary."""
        summary = results.get("summary", {})
        
        print("\n" + "=" * 70)
        print("FINAL SUMMARY")
        print("=" * 70)
        
        print(f"\nPERSON_CLUSTER: {summary.get('person_cluster', {}).get('pass_rate', '0/12')}")
        print(f"STATUS_CLUSTER: {summary.get('status_cluster', {}).get('pass_rate', '0/4')}")
        print(f"PRODUCT_CLUSTER: {summary.get('product_cluster', {}).get('pass_rate', '0/3')}")
        print(f"TOTAL_RECOVERED: {summary.get('total_recovered', {}).get('rate', '0/19')}")
        print(f"NEW_REGRESSIONS: {summary.get('new_regressions', 0)}")
        print(f"SOURCE_ORACLE: {summary.get('source_oracle', 'FAIL')}")
        print(f"READY_FOR_FULL_QA026: {summary.get('ready_for_full_qa026', 'NO')}")


async def main():
    runner = QA026V4TestRunner()
    
    async with runner as r:
        results = await r.run_targeted_retest()
    
    # Save results
    with open("qa_reports/CORE8_QA_026_V4_TARGETED_RETEST_RESULTS.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    runner.print_summary(results)
    
    print("\nResults saved to qa_reports/CORE8_QA_026_V4_TARGETED_RETEST_RESULTS.json")


if __name__ == "__main__":
    asyncio.run(main())
