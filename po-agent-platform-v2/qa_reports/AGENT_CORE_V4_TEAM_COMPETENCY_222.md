# AGENT CORE V4 — Repository-Backed Team Competency Gate (A222)

**Verdict:** `AGENT_CORE_V4_TEAM_COMPETENCY_RED_A222`
**Classification:** RED_COMPLETION_CONTRACT_REAL_EMPTY (first boundary) + load-join case mismatch (silently inactivates load ranking)

| Field | Value |
|---|---|
| START_HEAD | `8a74532ccb87b65054867693684af5792300f64d` |
| Owner implementation | `e7d9af4` (feat: activate repository-backed team competency matching in wave_batch3.py) + `d8bd40b` (tests) |
| A221R3 checkpoint | `84b0ae28aa4c37b0e502f92f08738fab66dbd4f6` (`checkpoint/v4-full-functional-green-a221r3`) |
| Affected skills | `team.competency_match`, `team.assignee_recommendation` only |
| Test agent | 8212, PID 10237 @ `8a74532` |
| Date | 2026-09-27 |

## Phase summary

| Phase | Result |
|---|---|
| P0 diff audit | **PASS** — plugin-only: `wave_batch3.py` is the only production change. No Core/planner/runtime/adapter/task-api diff. No tenant-scan path introduced. |
| P1 tests | **PASS-with-finding** — `219 passed, 1 failed`. The failure is a stale owner test asserting the OLD fail-closed behavior (see P1 note). The 3 new `test_agent_core_v4_team_competency_source.py` tests pass but mask both defects (see D-A222-1/D-A222-2). |
| P2 source integrity | **PASS** — 16 members; DMS=14, OLP=10; no numeric competency levels in any source file (all "требуют ручного подтверждения"); yaml/competencies.md/team.md mutually consistent. SHAs: team_members.yaml `e7d816e7cfda42cc`, competencies.md `8b22b6ff6cc40865`, team.md `b796f090afbf40b1`. All logins+ids valid. |
| P3 team.competency_match | **RED — first failing boundary** — DMS-380 3/3 COMPLETED (12 matches, top Agataeva.A.Z); OLP-3304 2/3 COMPLETED (1 match: Reshetnik.A) + 1 run planner-routed to team.assignee_recommendation (source-exact, non-blocking F1); **DMS-335 0/3 FAILED, DMS-432 0/3 FAILED** — all `v4 planner step budget exhausted without READY` (zero-overlap completion contract, D-A222-1). |
| P4 team.assignee_recommendation | **RED (D-A222-2)** — DMS-380 3/3 COMPLETED (rec=Agataeva.A.Z, 12 candidates, **ALL active_tasks/wip/blocked=0**); OLP-3304 2/2 COMPLETED (rec=Reshetnik.A, 1 candidate, load=0); DMS-335 2/2 FAILED (same D-A222-1 contract defect). |
| P5 identity/product filters | **PASS** — DMS-999999 → typed `v4_capability_unavailable` "REAL AS21 did not expose task DMS-999999" for both skills (4.4s/7.3s, bounded point read); DMS-380 matches exclude OLP-only members (Goncharov.A.O, Reshetnik.A absent); OLP-3304 returns only Reshetnik.A. No silent identity promotion. |
| P6 Browser C | **SKIPPED** — spec: "If RED: identify first failing boundary and STOP." |
| P7 retained Team regression | **PASS 7/7, A221R3 parity** (below). |
| P8 audit | **PASS** — window 12472–12527: local factual reads=0, fallback reads=0, mutations=0, tenant scans=0, task-query=0; 9 bounded point reads (DMS-335/380/432/999999, OLP-3304); 11 current-sprint calls, 16 sprint-collection calls, all space-scoped. Competency config reads are repository/config reads (team_members.yaml) — not visible in task-api log by design; task facts come only from bounded REAL AS21 reads. |

## D-A222-1 (first failing boundary, Phase 3): zero-overlap tasks cannot complete legitimately

**Behavior at the capability level is spec-correct.** For a token-disjoint task the capability returns `matches=[]` / `candidates=[]` with an honest typed warning (`no_declared_competency_match` / `insufficient_declared_competency_evidence`) and no fabrication — exactly what the spec's "if no overlap: valid empty/insufficient-evidence result" requires.

**The completion contract makes that legitimate empty result uncompletable:**

- `wave_batch3.py:366` — `CompletionRequirement("team.competency_match", data_keys=("space", "task_key", "matches"))`
- `wave_batch3.py:377` — `CompletionRequirement("team.assignee_recommendation", data_keys=("space", "task_key", "candidates"))`
- `agent_core_v4_completion.py:187-188` requires `_nonempty()` for every `data_key`; `_nonempty` (`:53-59`) returns `False` for `[]` (but `True` for scalar `0`).

→ deterministic completion blocked → planner forced to READY → READY rejected as unsatisfied → step budget exhausted → `v4_runtime_failure: v4 planner step budget exhausted without READY`.

**Proven live (deterministic, fail-closed, zero fabrication):**

| Case | Runs | Outcome |
|---|---|---|
| match DMS-335 | 3/3 FAILED | step budget exhausted (24–35s) |
| match DMS-432 | 3/3 FAILED | step budget exhausted (28–37s) |
| rec DMS-335 | 2/2 FAILED | step budget exhausted (14–23s) |

Zero-overlap ground truth (independent token simulation `qa_222_overlap_sim.py`): DMS-335 → 0 members, DMS-432 → 0 members.

**Defect class:** identical to A215F (zero-worklog sprints) — fixed there in A215F2 with REAL_EMPTY-safe scalar contract keys (`worklog_count`, where `_nonempty(0)=True`).

**Owner fix (proposed, not implemented):** add REAL_EMPTY-safe scalar key(s) to both contracts (e.g. `match_count` / `candidate_count` int, 0 allowed) mirroring the A215F2 precedent — and/or make the gate accept an empty collection accompanied by the typed insufficient-evidence warning as a legitimate terminal. Add a non-mocked regression with a token-disjoint task asserting `COMPLETED` + empty matches + warning.

## D-A222-2 (Phase 4): current-load join is always zero (case mismatch) — load ranking silently inactivated

- Load counters are keyed by `_member(task)` (`wave_batch3.py:30-38`, prefers `assignee_login`), which the production adapter maps from **lowercase** `user.login` (`adapters/task_api.py:392-431`, e.g. `moiseev.a.n`).
- Candidate rows look up by yaml `login` (**camelCase**, e.g. `Moiseev.A.N`) at `:190` via `load.get(login, 0)` / `wip.get(login, 0)` / `blocked.get(login, 0)` (`:196-198`) → the join never matches → **every candidate reports active_tasks=0, wip=0, blocked=0**.
- The spec-mandated deterministic sort (declared overlap desc → **active load asc → WIP asc → blocked asc** → login) degenerates: the three load criteria are uniformly zero; the recommendation is effectively decided by match_count + login tie-break only.

**Proven:** `qa_222_load_check.py` (clean production path): load dict keys are lowercase, yaml lookups camelCase → 0 for all members. Live P4 DMS-380: 12 candidates, all zeros — while the independent load oracle for DMS-SPRNT-3 (54 active) is: moiseev.a.n=10, agataeva.a.z=8, kondratchikova.p.i=8, dolgovskoy.e.n=7, garanin.r.v=7, unassigned=5, semavin.m.m=3, kuznetsov.m.se=2, alekseev.k.s=1, zhdanov.a.ni=1, makoshina.v.v=1, bezrukov.p.s=1.

**Why the owner's tests mask it:** the FakeAdapter in `test_agent_core_v4_team_competency_source.py` emits **camelCase** `assignee_login`, so the join "works" in the fake while the real adapter contract (lowercase login) is not mirrored.

**Owner fix (proposed):** case-insensitive join (normalize both sides, e.g. `casefold`) — do NOT change the adapter mapping (lowercase `assignee_login` is the certified contract used by all team.* skills). Add a non-mocked regression with production casing (lowercase assignee_login + camelCase yaml login) asserting load>0 for a known member.

**Scope note:** other team.* skills are unaffected — they use `_member` consistently on both sides (P7 parity exact, below).

## P1 test note

`tests/test_agent_core_v4_batch3.py::test_competency_and_assignee_recommendation_fail_closed_without_source` FAILED — it asserts the pre-A222 fail-closed terminal ("cannot be calculated … no repository competency source") and was not updated in `d8bd40b`. All 3 new source tests pass but only exercise the non-empty-overlap path with fake-cased members, masking D-A222-1 (no zero-overlap case) and D-A222-2 (camelCase fake login).

## P7 retained Team regression (7/7, A221R3 parity)

| Case | Result | Detail |
|---|---|---|
| team.workload | COMPLETED | 54 active / 19 completed / 5 unassigned / 13 members; per-member rows exact vs independent load oracle (moiseev 10, agataeva 8, kondratchikova 8, dolgovskoy 7, garanin 7, …). Completed 18→19 = verified live drift. |
| team.wip | COMPLETED | total_wip=31 exact; by_member exact (agataeva 6, moiseev 6, dolgovskoy 4, garanin 4, kondratchikova 3, unassigned 3, …); 31 task_keys. |
| team.blocked | COMPLETED | total_blocked=2 = [DMS-352, DMS-379] — A221R3/A208 identical. |
| team.capacity | FAILED (typed) | `v4_capability_unavailable` — source-backed estimates guard (A215B behavior retained, explicit 40h baseline preserved in args). |
| team.bottlenecks | COMPLETED | 9 bottlenecks (A221R3 DMS=9 rows). |
| team.distribution | COMPLETED | 73 tasks / 13 members, raw source status labels preserved. |
| member.time_spent (Semavin) | COMPLETED | 94.0h / 12 entries, by_task DMS-411=32, DMS-267=22, DMS-408=16, DMS-390=8, DMS-403=8, DMS-430=8; attribution=worklog_author_external_id. Drift from A220 (64h/8) verified via source point reads: DMS-411 32h/4 complete, DMS-430 8h/1 complete, DMS-267 total 38h/5 of which 22h are Semavin's (author-scoping semantics retained). |

## Non-blocking findings

- **F1:** match/OLP-3304 run #2 — planner routed "кто по компетенциям за OLP-3304" to `team.assignee_recommendation` (still source-exact: rec=Reshetnik.A). Known LLM planner routing non-determinism class (A215/A216 F1).
- **F2:** live drift DMS-SPRNT-3 completed 18→19 (73 total unchanged) — verified against source, not a defect.
- **F3:** member_time drift 64h/8 (A220, 09-26) → 94h/12 (A222, 09-27) — new source worklogs dated through 2026-09-27, verified by bounded point reads.

## Safety

0 local factual reads, 0 local fallback reads, 0 mutations, 0 tenant-wide scans, 0 unscoped task-query. 9 bounded point reads + 11 space-scoped current-sprint calls. Zero fabrication in every run (including all FAILED ones — typed fail-closed).

## Recommendation

**STOP** (per spec: first failing boundary identified — Phase 3, D-A222-1). No UI widget/state/lineage phase.

Re-gate (A222R) after owner fix:
1. D-A222-1: REAL_EMPTY-safe scalar contract keys (A215F2 precedent) + non-mocked zero-overlap regression → re-probe P3 DMS-335/DMS-432 (≥3 each, expect COMPLETED + empty matches + typed warning).
2. D-A222-2: case-insensitive load join + production-casing regression → re-probe P4 DMS-380 (expect load>0 matching the oracle; recommendation order must respect active-load ascending).
3. Update the stale `test_competency_and_assignee_recommendation_fail_closed_without_source`.
4. Full P1 suite, P6 Browser C, P7 parity re-confirm.

## Services

- agent 8212 (PID 10237 @ `8a74532`), task-api 8241, MCP-SWTR 3000, UI 5175 [::1] — left running.

## QA artifacts

- `qa_artifacts/a222_p2_source.json` — source integrity (SHAs, member counts, product membership)
- `qa_artifacts/a222_overlap_sim.json` — independent token-overlap simulation
- `qa_artifacts/a222_p3_p4.json` — P3/P4 live probe results (12 match + 8 rec runs)
- `qa_artifacts/a222_p5_support.json` — not-found + product-filter + bottlenecks member-case probes
- `qa_artifacts/a222_p7_team.json` — P7 retained regression payloads
- `qa_artifacts/a222_source_audit.json` — P8 task-api window audit
- Runners (repo root, uncommitted): `qa_222_overlap_sim.py`, `qa_222_p3_p4.py`, `qa_222_p5_support.py`, `qa_222_p7_team.py`, `qa_222_p8_audit.py`, `qa_222_load_check.py`
