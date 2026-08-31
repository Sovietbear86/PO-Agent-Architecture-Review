#!/usr/bin/env python3
"""Simple correction trace script for Assignment 072."""

import httpx
import json

def query(query_text, session_id="test"):
    resp = httpx.post(
        "http://127.0.0.1:8004/api/v1/query",
        json={"query": query_text, "session_id": session_id},
        timeout=30
    )
    return resp.json()

def print_slots(r, turn=1):
    data = r.get("data", {})
    sf = data.get("semantic_frame", {})
    print(f"  Turn {turn}:")
    print(f"    status: {r.get('status')}")
    print(f"    slots:")
    for k in ["person_raw", "member_login", "sprint_id", "status_raw", "status_semantic", "dialogue_act"]:
        print(f"      {k}: {sf.get(k, 'N/A')}")
    return sf

def run_session(name: str):
    print(f"\n=== Session: {name} ===")
    
    # Turn 1
    r1 = query("Покажи задачи Гаранина в DMS со статусом todo", name)
    s1 = print_slots(r1, 1)
    
    # Turn 2 - correction
    r2 = query("Покажи задачи Гаранина в DMS со статусом in progress", name)
    s2 = print_slots(r2, 2)
    
    # Check invariants
    print(f"\n  Invariants:")
    print(f"    person_raw preserved: {s1.get('person_raw') == s2.get('person_raw')}")
    print(f"    sprint_id preserved: {s1.get('sprint_id') == s2.get('sprint_id')}")
    print(f"    status_raw updated: {s2.get('status_raw') == 'in progress'}")
    print(f"    member_login valid: {s2.get('member_login', 'MISSING')}")
    print(f"    status_semantic corrupted: {'Покажи задачи' in s2.get('status_semantic', '')}")

print("Phase 1: Reproduce ×3")
print("=" * 60)

run_session("corr_072_s1")
run_session("corr_072_s2")
run_session("corr_072_s3")

print("\n" + "=" * 60)
print("Phase 1 complete - check for corruption patterns above")
