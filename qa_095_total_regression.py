#!/usr/bin/env python3
"""Total Real-Agent Backend Certification - Assignment 095."""

import httpx
import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

PO_AGENT_URL = "http://127.0.0.1:8004"
LEARNED_POLICY_PATH = Path(".po_agent/learned_policies.json")

@dataclass
class SkillTestResult:
    skill_id: str
    version: str
    canonical_query: str
    canonical_result: str
    paraphrase_query: str
    paraphrase_result: str
    edge_query: str
    edge_result: str
    real_source_evidence: str
    learning_applicable: bool
    learning_proof: Optional[str]
    restart_evidence: Optional[str]
    rollback_evidence: Optional[str]
    status: str  # PASS/FAIL/BLOCKED
    reason: str = ""

@dataclass
class TestReport:
    head_sha: str
    runtime_mode: Dict[str, Any]
    skill_catalog: List[SkillTestResult]
    source_counters: Dict[str, int]
    learning_loop_results: Dict[str, Any]
    automated_test_results: Dict[str, Any]
    final_verdict: str
    first_failing_boundary: Optional[str] = None

def query(query_text: str, session_id: str) -> dict:
    """Execute a query against PO Agent."""
    resp = httpx.post(
        f"{PO_AGENT_URL}/api/v1/query",
        json={"query": query_text, "session_id": session_id},
        timeout=30
    )
    return resp.json()

def get_health() -> dict:
    """Get runtime health status."""
    resp = httpx.get(f"{PO_AGENT_URL}/health", timeout=5)
    return resp.json()

def get_policy_store() -> list:
    """Load current policy store."""
    if not LEARNED_POLICY_PATH.exists():
        return []
    with open(LEARNED_POLICY_PATH) as f:
        return json.load(f)

def get_active_policies() -> list:
    """Get active policies."""
    return [p for p in get_policy_store() if p.get('state') == 'promoted']

def create_fresh_policy(skill_id: str, session: str) -> Optional[dict]:
    """Create a fresh learning policy via correction pattern."""
    from po_agent.harness.learned_policy import LearnedPolicyStore
    
    # Rollback any active policy
    store = LearnedPolicyStore()
    try:
        store.rollback(skill_id, reason='095_fresh_policy')
    except Exception:
        pass  # No active policy to rollback
    
    time.sleep(1)
    
    # Negative query
    negative = f"Покажи задачи {skill_id}-NONEXISTENT"
    r1 = query(negative, f"{skill_id}_neg")
    
    time.sleep(1)
    
    # Correction - use real task
    r2 = query(f"Покажи задачи DMS-100", f"{skill_id}_pos")
    
    time.sleep(2)
    
    # Check if policy was created
    with open(LEARNED_POLICY_PATH) as f:
        data = json.load(f)
    
    active = [p for p in data if p['skill_id'] == skill_id and p['state'] == 'promoted']
    return active[0] if active else None

def test_skill_canonical(skill_id: str, canonical_query: str, session: str) -> dict:
    """Test a skill with canonical query."""
    r = query(canonical_query, session)
    return {
        "status": r.get("status"),
        "skill": r.get("skill"),
        "answer": r.get("answer", "")[:100],
        "skill_id": r.get("skill", {}).get("id") if r.get("skill") else None,
    }

def main():
    print("=" * 60)
    print("Assignment 095 — Total Real-Agent Backend Certification")
    print("=" * 60)
    
    # Phase 0: Runtime truth
    print("\nPhase 0: Runtime Truth")
    print("-" * 40)
    
    health = get_health()
    print(f"Runtime mode: {health.get('adapter')} + {health.get('source_status')}")
    print(f"Source facts: {health.get('source_facts', [])}")
    print(f"Skills ready: {health.get('skill_readiness', {}).get('ready', 0)}")
    print(f"Skills unavailable: {health.get('skill_readiness', {}).get('unavailable', 0)}")
    
    policies = get_policy_store()
    print(f"Policy store: {len(policies)} policies, {len(get_active_policies())} active")
    
    # Phase 1: Discover skill catalog
    print("\nPhase 1: Skill Catalog Discovery")
    print("-" * 40)
    
    from po_agent.harness.skill_catalog import SKILL_CATALOG, catalog_by_id
    
    catalog = catalog_by_id()
    print(f"Total skills in catalog: {len(SKILL_CATALOG)}")
    print(f"Implemented skills: {sum(1 for s in SKILL_CATALOG if s.status == 'implemented')}")
    
    # Phase 2: Functional certification (sample)
    print("\nPhase 2: Functional Black-Box Certification")
    print("-" * 40)
    
    # Test sample skills
    test_skills = [
        ("task-lookup", "Покажи задачи DMS-100", "DMS-100 lookup"),
        ("sprint-health", "Покажи здоровье спринта DMS-SPRNT-1", "sprint health"),
        ("release-health", "Покажи здоровье релиза", "release health"),
        ("team-workload", "Покажи нагрузку команды", "team workload"),
    ]
    
    for skill_id, query_text, desc in test_skills:
        r = query(query_text, f"cert_{skill_id}")
        status = r.get("status")
        skill = r.get("skill", {}).get("id") if r.get("skill") else None
        print(f"{skill_id}: {status} (skill={skill})")
    
    # Phase 5: Learning Loop (sample)
    print("\nPhase 5: Learning Loop Applicability")
    print("-" * 40)
    
    for skill_id, query_text, desc in test_skills[:2]:
        print(f"Testing {skill_id}...")
        policy = create_fresh_policy(skill_id, f"learning_{skill_id}")
        if policy:
            print(f"  Policy created: {policy['policy_id']}")
        else:
            print(f"  No policy created for {skill_id}")

if __name__ == "__main__":
    main()
