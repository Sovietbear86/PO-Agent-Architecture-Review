"""Assignment 183 Phase 4 — live REAL integration validation via fresh PO Agent 8019."""
import time, uuid, json, httpx

AGENT = "http://127.0.0.1:8019"


def run_query(query: str, *, timeout: int = 240) -> dict:
    body = json.dumps({"query": query, "session_id": str(uuid.uuid4())}).encode()
    t0 = time.perf_counter()
    r = httpx.post(
        f"{AGENT}/api/v1/query-v4",
        content=body,
        headers={"Content-Type": "application/json", "X-Session-Id": str(uuid.uuid4())},
        timeout=timeout,
    )
    dt = time.perf_counter() - t0
    d = r.json()
    meta = (d.get("data") or {}).get("_agent_core_v4", {})
    traj = meta.get("trajectory", []) or []
    caps = [t.get("capability_id") or t.get("skill_id") for t in traj]
    adjusts = [t.get("skill_adjustment") for t in traj if t.get("skill_adjustment")]
    d["_caps"] = caps
    d["_skill_adjustments"] = adjusts
    d["_latency_s"] = round(dt, 1)
    return d


def task_keys(d: dict):
    keys = []
    for step in (d.get("data") or {}).get("results", []) or []:
        data = step.get("data") or {}
        if isinstance(data, dict):
            tk = data.get("task_keys") or data.get("task_keys_sample") or []
            keys.extend(k for k in tk if k)
    return keys


def sprint_of(d: dict):
    for step in (d.get("data") or {}).get("results", []) or []:
        data = step.get("data") or {}
        if isinstance(data, dict) and data.get("sprint_id"):
            return data.get("sprint_id")
    return None


def resolved_login(d: dict):
    for step in (d.get("data") or {}).get("results", []) or []:
        if step.get("capability_id") == "member.resolve":
            data = step.get("data") or {}
            if isinstance(data, dict) and data.get("member_login"):
                return data.get("member_login")
    return None


def main():
    out = {}

    # A) transport probe: large assignee collection through the long-lived runtime
    probe = []
    for i in range(2):
        res = run_query("Задачи Семавина")
        keys = task_keys(res)
        probe.append({
            "status": res.get("status"), "task_count": len(keys),
            "caps": res["_caps"], "warnings": res.get("warnings"), "latency_s": res["_latency_s"],
        })
        print(f"[A{i+1}] semavin: {res.get('status')} count={len(keys)} {res['_latency_s']}s {res.get('warnings')}")
    out["transport_probe"] = probe

    # B) period -> sprint -> open tasks (August sprint DMS)
    res = run_query("Открытые задачи Александра Жданова в августовском спринте DMS")
    keys = task_keys(res)
    out["zhdanov_august"] = {
        "status": res.get("status"), "sprint": sprint_of(res), "task_count": len(keys),
        "caps": res["_caps"], "answer": res.get("answer"), "warnings": res.get("warnings"),
        "latency_s": res["_latency_s"],
    }
    print(f"[B] zhdanov-august: {res.get('status')} sprint={sprint_of(res)} count={len(keys)} caps={res['_caps']} {res['_latency_s']}s")
    print("    answer:", res.get("answer"))

    # C) plural active sprints (must be the full collection, not a singleton)
    res = run_query("Активные спринты в DMS")
    sprints = []
    for step in (res.get("data") or {}).get("results", []) or []:
        data = step.get("data") or {}
        if isinstance(data, dict) and isinstance(data.get("sprints"), list):
            sprints = [s.get("code") for s in data["sprints"]]
    out["active_sprints"] = {
        "status": res.get("status"), "sprints": sprints,
        "skill_adjustments": res["_skill_adjustments"],
        "caps": res["_caps"], "answer": res.get("answer"), "warnings": res.get("warnings"),
        "latency_s": res["_latency_s"],
    }
    print(f"[C] active sprints: {res.get('status')} sprints={sprints} adjust={res['_skill_adjustments']} caps={res['_caps']} {res['_latency_s']}s")
    print("    answer:", res.get("answer"))

    # D) non-roster person (Ivanov) in DMS-SPRNT-2
    res = run_query("Покажи открытые задачи Петра Иванова в спринте DMS-SPRNT-2")
    keys = task_keys(res)
    out["petr_ivanov"] = {
        "status": res.get("status"), "resolved_login": resolved_login(res),
        "sprint": sprint_of(res), "task_count": len(keys),
        "caps": res["_caps"], "answer": res.get("answer"), "warnings": res.get("warnings"),
        "latency_s": res["_latency_s"],
    }
    print(f"[D] petr ivanov: {res.get('status')} login={resolved_login(res)} count={len(keys)} caps={res['_caps']} {res['_latency_s']}s")
    print("    answer:", res.get("answer"))

    print("\n=== PHASE4 SUMMARY ===")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    with open("qa_183_phase4_results.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()