#!/usr/bin/env python3
"""Regression matrix test for Assignment 072 fix."""

import httpx
import sys

def query(query_text, session_id="reg_test"):
    try:
        resp = httpx.post(
            "http://127.0.0.1:8004/api/v1/query",
            json={"query": query_text, "session_id": session_id},
            timeout=30
        )
        return resp.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_slots(r):
    if not r:
        return {}
    return r.get("data", {}).get("semantic_frame", {}).get("slots", {})

def check_invariants(r1, r2, session_name):
    """Check invariants for correction scenario."""
    if not r1 or not r2:
        print(f"  {session_name}: FAIL - null response")
        return False
    
    s1 = get_slots(r1)
    s2 = get_slots(r2)
    
    # Check invariants
    checks = {
        "person_raw preserved": s1.get("person_raw") == s2.get("person_raw"),
        "status_raw updated": s2.get("status_raw") == "in progress",
        "member_login valid": "Покажи задачи" not in (s2.get("member_login") or ""),
        "status_semantic clean": "Покажи задачи" not in (s2.get("status_semantic") or ""),
    }
    
    all_passed = all(checks.values())
    print(f"  {session_name}: {'PASS' if all_passed else 'FAIL'}")
    for name, passed in checks.items():
        if not passed:
            print(f"    FAIL: {name}")
    
    return all_passed

def run_test(name, queries, session_id, expected_status_raw=None):
    """Run a test scenario."""
    print(f"\n=== {name} ===")
    
    if isinstance(queries, str):
        queries = [queries]
    
    results = []
    for q in queries:
        r = query(q, session_id)
        if not r:
            print(f"  FAIL: null response for query: {q[:50]}...")
            return False
        results.append(r)
        print(f"  Query: {q[:60]}...")
        print(f"    status_raw: {get_slots(r).get('status_raw', 'N/A')}")
        print(f"    member_login: {get_slots(r).get('member_login', 'N/A')}")
        print(f"    status: {r.get('status')}")
    
    # Check expected status_raw if provided
    if expected_status_raw and results:
        last_status = get_slots(results[-1]).get("status_raw")
        if last_status != expected_status_raw:
            print(f"  FAIL: expected status_raw='{expected_status_raw}', got '{last_status}'")
            return False
    
    return True

print("=" * 60)
print("Phase 5: Regression Matrix")
print("=" * 60)

all_passed = True

# Test 1: Person-only
all_passed &= run_test(
    "1. Person-only",
    "Покажи задачи Гаранина",
    "reg_1",
    expected_status_raw=None
)

# Test 2: Sprint-id (use a real proven sprint)
all_passed &= run_test(
    "2. Sprint-id",
    "Покажи задачи в DMS-SPRNT-2",
    "reg_2",
    expected_status_raw=None
)

# Test 3: Exact task-id
all_passed &= run_test(
    "3. Exact task-id",
    "Покажи задачу DMS-271",
    "reg_3",
    expected_status_raw=None
)

# Test 4: Status query
all_passed &= run_test(
    "4. Status query",
    "Покажи задачи со статусом todo",
    "reg_4",
    expected_status_raw="todo"
)

# Test 5: Combined person+product+status (correction scenario)
all_passed &= run_test(
    "5. Combined person+product+status",
    [
        "Покажи задачи Гаранина в DMS со статусом todo",
        "Покажи задачи Гаранина в DMS со статусом in progress"
    ],
    "reg_5"
)

# Test 6: Correction scenario from assignment
all_passed &= run_test(
    "6. Correction scenario",
    [
        "Покажи задачи Гаранина в DMS со статусом todo",
        "Покажи задачи Гаранина в DMS со статусом in progress"
    ],
    "reg_6"
)

# Test 7: Second member correction flow
all_passed &= run_test(
    "7. Second member correction",
    [
        "Покажи задачи Родиона Гаранина в DMS со статусом todo",
        "Покажи задачи Родиона Гаранина в DMS со статусом in progress"
    ],
    "reg_7"
)

print("\n" + "=" * 60)
print(f"Regression matrix: {'PASS' if all_passed else 'FAIL'}")
print("=" * 60)

sys.exit(0 if all_passed else 1)
