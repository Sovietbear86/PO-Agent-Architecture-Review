#!/usr/bin/env python3
"""QA report generation script for Assignment 072D."""

import httpx
import json
import sys

def query(query_text, session_id="test"):
    resp = httpx.post(
        "http://127.0.0.1:8004/api/v1/query",
        json={"query": query_text, "session_id": session_id},
        timeout=30
    )
    return resp.json()

def get_slots(r):
    """Extract slots from response - handles both old and new structure."""
    data = r.get("data", {})
    sf = data.get("semantic_frame", {})
    
    # Check if slots is a dict inside semantic_frame
    if isinstance(sf, dict) and "slots" in sf and isinstance(sf["slots"], dict):
        return sf["slots"]
    
    # Otherwise, fields are directly in semantic_frame
    if isinstance(sf, dict):
        return sf
    
    return {}

def run_correction_test(session_id: str, member_name: str):
    """Run a correction test with given session ID."""
    print(f"\n=== Session: {session_id} ===")
    
    # Turn 1
    r1 = query(f"Покажи задачи {member_name} в DMS со статусом todo", session_id)
    s1 = get_slots(r1)
    print(f"  Turn 1:")
    print(f"    status: {r1.get('status')}")
    print(f"    slots:")
    for k in ["person_raw", "member_login", "sprint_id", "status_raw", "status_semantic", "dialogue_act"]:
        print(f"      {k}: {s1.get(k, 'N/A')}")
    
    # Turn 2 - correction
    r2 = query(f"Покажи задачи {member_name} в DMS со статусом in progress", session_id)
    s2 = get_slots(r2)
    print(f"  Turn 2:")
    print(f"    status: {r2.get('status')}")
    print(f"    slots:")
    for k in ["person_raw", "member_login", "sprint_id", "status_raw", "status_semantic", "dialogue_act"]:
        print(f"      {k}: {s2.get(k, 'N/A')}")
    
    # Check invariants
    print(f"\n  Invariants:")
    print(f"    person_raw preserved: {s1.get('person_raw') == s2.get('person_raw')}")
    print(f"    sprint_id preserved: {s1.get('sprint_id') == s2.get('sprint_id')}")
    print(f"    status_raw updated: {s2.get('status_raw') == 'in progress'}")
    print(f"    member_login valid: {'MISSING' if not s2.get('member_login') else s2.get('member_login')}")
    print(f"    status_semantic clean: {'Покажи задачи' not in str(s2.get('status_semantic', ''))}")
    
    return s1, s2

def check_clarification_state(r):
    """Check pending clarification state."""
    return {
        "clarification_id": r.get("clarification_id"),
        "missing_field": r.get("data", {}).get("missing_field"),
        "question": r.get("question"),
        "status": r.get("status")
    }

print("=" * 60)
print("Assignment 072D - Correction Regression Test")
print("=" * 60)

# Phase 1: Correction regression with 3 sessions
print("\nPhase 1: Correction Regression ×3")
print("-" * 40)

run_correction_test("072d_s1", "Гаранина")
run_correction_test("072d_s2", "Гаранина")
run_correction_test("072d_s3", "Гаранина")

# Phase 1b: Second member
print("\nPhase 1b: Second Member Correction")
print("-" * 40)

run_correction_test("072d_garanin2", "Родиона Гаранина")

print("\n" + "=" * 60)
print("Phase 1 complete")
print("=" * 60)
