#!/usr/bin/env python3
"""QA report generation script for Assignment 072E - Persistent Learning Loop proof."""

import httpx
import json
import os
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
    """Load current policy store state."""
    if not PO_AGENT_LEARNED_POLICY_PATH.exists():
        return []
    with open(PO_AGENT_LEARNED_POLICY_PATH) as f:
        return json.load(f)

def get_active_policies():
    """Get active policies only."""
    return [p for p in get_policy_store() if is_policy_active(p)]

def is_policy_active(p):
    """Check if policy is active based on state and behaviour."""
    return p.get('state') == 'promoted' and p.get('behaviour') == 'authoritative_recheck_on_negative'

def show_policy_state():
    """Display current policy state."""
    print("\n=== Policy Store State ===")
    policies = get_policy_store()
    print(f"Total policies: {len(policies)}")
    for p in policies:
        print(f"  {p['policy_id']}: state={p['state']}, version={p['version']}, skill={p['skill_id']}, active={is_policy_active(p)}")
    print()

def run_learning_test():
    """Run the full Learning Loop test."""
    
    print("=" * 60)
    print("Assignment 072E — Persistent Learning Loop Proof")
    print("=" * 60)
    
    # Phase 1: Establish baseline
    print("\nPhase 1: Establish Policy-Store Baseline")
    print("-" * 40)
    show_policy_state()
    baseline_count = len(get_active_policies())
    print(f"Active policies before learning: {baseline_count}")
    
    # Phase 2: Trigger learning with correction
    print("\nPhase 2: Trigger Real Bounded Learning")
    print("-" * 40)
    
    # Use task-lookup with an invalid task key first, then correct
    session = "learning_072e_1"
    
    # Initial negative - query for a non-existent task
    print(f"\n--- Initial execution (negative) ---")
    r1 = query('Покажи задачи DMS-NONEXISTENT', session)
    print(f"Query: Покажи задачи DMS-NONEXISTENT")
    print(f"Status: {r1.get('status')}")
    print(f"Answer: {r1.get('answer')}")
    print(f"Warnings: {r1.get('warnings', [])}")
    
    # Wait a moment for any async operations
    time.sleep(1)
    
    # Show policy state before correction
    print("\n--- Before correction ---")
    show_policy_state()
    
    # Correction - actual valid task
    print(f"\n--- Correction (authoritative recheck) ---")
    r2 = query('Покажи задачи DMS-100', session)
    print(f"Query: Покажи задачи DMS-100")
    print(f"Status: {r2.get('status')}")
    print(f"Answer: {r2.get('answer')[:100] if r2.get('answer') else 'N/A'}...")
    print(f"Skill: {r2.get('skill', {})}")
    
    # Wait for persistence
    time.sleep(2)
    
    # Check policy state after correction
    print("\n--- After correction ---")
    show_policy_state()
    after_count = len(get_active_policies())
    print(f"Active policies after correction: {after_count}")
    
    # Phase 3: Prove generalization
    print("\nPhase 3: Prove Generalization")
    print("-" * 40)
    
    # Use different session, same skill, different query
    session2 = "learning_072e_2"
    print(f"\n--- Generalization test (different query) ---")
    r3 = query('Покажи задачи DMS-200', session2)
    print(f"Query: Покажи задачи DMS-200")
    print(f"Status: {r3.get('status')}")
    print(f"Answer: {r3.get('answer')[:100] if r3.get('answer') else 'N/A'}...")
    print(f"Skill: {r3.get('skill', {})}")
    
    # Check policy still active
    show_policy_state()
    
    # Phase 4: Cold restart
    print("\nPhase 4: Genuine Cold Restart")
    print("-" * 40)
    print("NOTE: Process restart required. Manual intervention needed.")
    print("Current PIDs would be captured here, then service restarted, then verified.")
    
    # Phase 5: Rollback
    print("\nPhase 5: Rollback and Negative Proof")
    print("-" * 40)
    print("NOTE: Rollback mechanism exists in LearnedPolicyStore.rollback()")
    print("Would call: store.rollback('task-lookup', reason='assignment_072e_test')")

if __name__ == "__main__":
    run_learning_test()
