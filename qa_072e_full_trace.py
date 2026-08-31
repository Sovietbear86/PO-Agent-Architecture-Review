#!/usr/bin/env python3
"""Full Learning Loop trace for Assignment 072E."""

import httpx
import json
import os
import sys
import time
from pathlib import Path

PO_AGENT_LEARNED_POLICY_PATH = Path(os.getenv("PO_AGENT_LEARNED_POLICY_PATH", ".po_agent/learned_policies.json"))

def query(query_text, session_id="test"):
    resp = httpx.post(
        "http://127.0.0.1:8004/api/v1/query",
        json={"query": query_text, "session_id": session_id},
        timeout=30
    )
    return resp.json()

def get_policy_store():
    if not PO_AGENT_LEARNED_POLICY_PATH.exists():
        return []
    with open(PO_AGENT_LEARNED_POLICY_PATH) as f:
        return json.load(f)

def is_policy_active(p):
    return p.get('state') == 'promoted' and p.get('behaviour') == 'authoritative_recheck_on_negative'

def get_active_policies():
    return [p for p in get_policy_store() if is_policy_active(p)]

def rollback_policy(skill_id: str, reason: str):
    """Manually rollback a policy using LearnedPolicyStore API."""
    from po_agent.harness.learned_policy import LearnedPolicyStore
    store = LearnedPolicyStore()
    return store.rollback(skill_id, reason=reason)

def save_baseline():
    """Save baseline state before test."""
    baseline = get_policy_store()
    with open('.po_agent/learned_policies_before_072e.json', 'w') as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)
    print(f"Baseline saved: {len(baseline)} policies")

def show_policy_state():
    policies = get_policy_store()
    print(f"\n  Total policies: {len(policies)}")
    print(f"  Active policies: {len(get_active_policies())}")
    for p in policies:
        print(f"    {p['policy_id']}: state={p['state']}, version={p['version']}, skill={p['skill_id']}")
    return policies

def run_full_learning_trace():
    print("=" * 60)
    print("Assignment 072E — Persistent Learning Loop Proof")
    print("=" * 60)
    
    # Phase 0: Baseline
    print("\nPhase 0: Provenance")
    print("-" * 40)
    print(f"Policy store path: {PO_AGENT_LEARNED_POLICY_PATH}")
    save_baseline()
    
    # Phase 1: Baseline state
    print("\nPhase 1: Establish Policy-Store Baseline")
    print("-" * 40)
    policies = show_policy_state()
    
    # We have task-lookup:authoritative_recheck_on_negative:v1
    skill_id = "task-lookup"
    existing_policy = next((p for p in policies if p['skill_id'] == skill_id and is_policy_active(p)), None)
    
    if existing_policy:
        print(f"\n  Existing active policy found: {existing_policy['policy_id']}")
        print(f"  Rolling back to create fresh test...")
        
        # Rollback existing policy
        try:
            rolled_back = rollback_policy(skill_id, "assignment_072e_test_fresh_start")
            print(f"  Rolled back: {rolled_back.policy_id}")
            print(f"  New state: {rolled_back.state}, reason: {rolled_back.rollback_reason}")
        except Exception as e:
            print(f"  ERROR during rollback: {e}")
            return
    
    # Show state after rollback
    print("\n  After rollback:")
    policies = show_policy_state()
    
    # Phase 2: Trigger learning with correction
    print("\nPhase 2: Trigger Real Bounded Learning")
    print("-" * 40)
    
    session = "learning_072e_1"
    
    # Initial negative - query for a non-existent task
    print(f"\n--- Initial execution (negative) ---")
    print(f"Query: Покажи задачи DMS-NONEXISTENT")
    r1 = query('Покажи задачи DMS-NONEXISTENT', session)
    print(f"Status: {r1.get('status')}")
    print(f"Answer: {r1.get('answer')}")
    print(f"Warnings: {r1.get('warnings', [])}")
    
    time.sleep(1)
    
    # Before correction
    print("\n--- Before correction ---")
    policies = show_policy_state()
    
    # Correction - actual valid task
    print(f"\n--- Correction (authoritative recheck) ---")
    print(f"Query: Покажи задачи DMS-100")
    r2 = query('Покажи задачи DMS-100', session)
    print(f"Status: {r2.get('status')}")
    answer = r2.get('answer', '')[:100]
    print(f"Answer: {answer}...")
    print(f"Skill: {r2.get('skill', {})}")
    
    time.sleep(2)
    
    # After correction
    print("\n--- After correction ---")
    policies = show_policy_state()
    
    # Phase 3: Prove generalization
    print("\nPhase 3: Prove Generalization")
    print("-" * 40)
    
    session2 = "learning_072e_2"
    print(f"\n--- Generalization test (different query) ---")
    print(f"Query: Покажи задачи DMS-200")
    r3 = query('Покажи задачи DMS-200', session2)
    print(f"Status: {r3.get('status')}")
    answer = r3.get('answer', '')[:100]
    print(f"Answer: {answer}...")
    print(f"Skill: {r3.get('skill', {})}")
    
    policies = show_policy_state()
    
    # Phase 4: Cold restart
    print("\nPhase 4: Genuine Cold Restart")
    print("-" * 40)
    print("NOTE: Process restart required. Manual intervention needed.")
    print("To complete this test:")
    print("  1. Record current PO Agent PID from lsof -ti:8004")
    print("  2. Stop service: kill <PID>")
    print("  3. Restart: uvicorn po_agent.main:app --host 127.0.0.1 --port 8004")
    print("  4. Re-run query to verify policy reloads")
    
    # Phase 5: Rollback
    print("\nPhase 5: Rollback and Negative Proof")
    print("-" * 40)
    
    print("\n--- Rolling back policy ---")
    try:
        rolled_back = rollback_policy(skill_id, "assignment_072e_test_rollback")
        print(f"Rolled back: {rolled_back.policy_id}")
        print(f"State: {rolled_back.state}, reason: {rolled_back.rollback_reason}")
    except Exception as e:
        print(f"ERROR during rollback: {e}")
        return
    
    print("\n--- After rollback ---")
    policies = show_policy_state()
    
    # Verify policy no longer active
    active = get_active_policies()
    print(f"\nActive policies after rollback: {len(active)}")
    
    # Final verification - query after rollback
    session3 = "learning_072e_3"
    print(f"\n--- Query after rollback ---")
    print(f"Query: Покажи задачи DMS-300")
    r4 = query('Покажи задачи DMS-300', session3)
    print(f"Status: {r4.get('status')}")
    print(f"Skill: {r4.get('skill', {})}")
    
    # Phase 6: Summary
    print("\nPhase 6: Summary")
    print("-" * 40)
    
    final_policies = get_policy_store()
    print(f"\nFinal policy store contains {len(final_policies)} policies:")
    for p in final_policies:
        print(f"  - {p['policy_id']}: state={p['state']}, version={p['version']}")
    
    # Check for policy created during test
    test_policies = [p for p in final_policies if p.get('correction_trace_id')]
    print(f"\nPolicies with correction_trace_id (created during test): {len(test_policies)}")

if __name__ == "__main__":
    run_full_learning_trace()
