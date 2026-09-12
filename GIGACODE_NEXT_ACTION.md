# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_184_V4_REPRESENTATIVE_POC_RECHECK`

## Mission
Assignment 183 was an **owner** hardening pass. It is now complete. This is a **QA-only**
re-run of the representative Agent Core v4 POC decision gate that Assignment 182 left
`BLOCKED_BY_PROVEN_SOURCE_OUTAGE`, plus the three live user scenarios that exposed generic
capability/governance gaps. **Do not restart or modify the V4 POC. Do not edit production.**

Assignment 183 shipped three generalized owner fixes on the current V4 architecture:
1. **Source transport reliability** — bounded resilient read-through for
   `/api/v1/swtr-read/` paths (`90 s` timeout + `3` bounded attempts + backoff + client
   refresh on transient timeout/connection failure), preserving exact source results and
   fail-closed behavior. This is the direct remediation for the 182 `assignee-tasks`
   read-through 30 s ceiling.
2. **Generic sprint discovery/list** — new `sprint.search` (human period → source-backed
   canonical sprint, typed ambiguity on multi-match) and `sprint.list` (source-backed
   active sprint collection), plus plural governance so a plural/list request is not
   silently satisfied by the `sprint.current` singleton.
3. **Source-authority identity governance** — a REAL/source-backed `member.resolve`
   identity is trusted downstream and the local roster no longer vetoes an unambiguous
   non-roster source identity, while anti-invention (no invented logins/ids) is preserved.

Your job: prove — on a fresh runtime against the freshest REAL AS21 — that (a) the blocked
10× DMS-380 decision gate now completes with exact source parity, (b) the mixed
representative generalization matrix passes, (c) the three previously failing user
scenarios are fixed and correct, and (d) safety/governance (fail-closed, no fabrication)
is preserved. Then deliver a final architecture verdict.

## Absolute rules (QA role)
- First: `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
- Read, in order, before running anything:
  - `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_FINAL_POC_DECISION_182.md`
  - `AGENT_CORE_V4_SKILL_NATIVE_SPEC.md` and `po-agent-platform-v2/docs/v4_dod/V4_DOD_LOCK.md`
  - Assignment 183 owner artifacts: `qa_183_phase4_results.json`, `qa_183_phase4_runner.py`
- **QA-only.** Do NOT modify: production code (`src/`), prompts, adapters, tests,
  fixtures, runtime config, model/provider, skill catalog, learning data, or AS21/SWTR
  data. Do NOT commit anything except the single QA report file below.
- **No full tenant-wide task sync.**
- **Stale-runtime rule:** do not reuse stale PO Agent ports `8004–8019`. Start a **fresh**
  PO Agent from test base HEAD on a **fresh port** (recommended `8020`+, next free).
- Concurrency `1`. Fresh session per run. Long agent call ≤ `600 s`.
- **REAL AS21 is authoritative.** Refresh every expected value (task counts, sprint ids,
  member logins) from a fresh Oracle B at run time. **Do not hardcode** `306`, `DMS-SPRNT-1/2`,
  `semavin.m.m`, `Ivanov.P.Se`, or any prior-run count as an assertion — compare the agent
  against a freshly built Oracle B in the same run.
- Preserve fail-closed semantics; never treat a source outage as an empty/fabricated result.

## Test environment (expected, verify at runtime)
- **Test base HEAD:** `8903db3` (Assignment 183 complete; groups 1–4 committed).
- **Owner commits under test (must be ancestors of HEAD):**
  - `796c466` — Phase 1: bounded resilient transport (`_get_resilient`, `_refresh_client`)
  - `a4fce91` — Phase 2: sprint discovery/list + plural governance + `V4CapabilityUnavailable`
  - `7be4e6b` — Phase 3: source-authority identity governance
  - `814ab44` — Assignment 183 spec (context only)
- **Model/provider:** `Qwen/Qwen3.8-27B` (unchanged).
- **Env:** `PO_AGENT_AGENT_CORE_V4_ENABLED=true`, `PO_AGENT_AS21_MODE=task-api`,
  `PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:<task-api-port>`.
- **Services:** Task API (SSE → MCP-SWTR) + MCP-SWTR (`http://127.0.0.1:3000/sse`, 48 tools)
  → REAL AS21. Confirm `agent_core_v4_ready=true` and `adapter=task-api`, `source_status=healthy`
  from the fresh agent `/health` before running gates.
- **Reference (optional):** Assignment 183 left a fresh agent on `8019` (task-api `8013`,
  MCP-SWTR `3000`) built from `8903db3`. You MAY reuse it **only** if you verify its
  `agent_core_v4_ready=true` and that it was started from `8903db3`; otherwise start your own
  fresh instance on a fresh port.

---

## Phase 0 — Focused build/protocol gate (regression net)
1. Run the V4 + transport + sprint + identity focused suites and confirm GREEN:
   ```
   cd po-agent-platform-v2
   ./.venv/bin/python -m pytest -q \
     tests/test_adapter_transport_resilience.py \
     tests/test_agent_core_v4_sprint_discovery.py \
     tests/test_agent_core_v4_identity_governance.py \
     tests/test_agent_core_v4_skill_native.py \
     tests/test_agent_core_v4_robust_protocol.py \
     tests/test_agent_core_v4_reliable.py
   ```
   (All should pass; record counts.)
2. Static invariants (script or direct inspection):
   - Production V4 runtime uses the robust/action-only planner path.
   - `semantic_prepass_used` is always `false` on the V4 path (no prepass call-site).
   - The three owner fixes introduce **no** entity/phrase/person/surname/trajectory
     hardcode in production `src/` (diff `814ab44..8903db3`).
   - `sprint.search`/`sprint.list` are present in the V4 catalog (16 capabilities expected:
     prior 14 + `sprint.search` + `sprint.list`).
   - Action-only recovery still rejects a recovery-minted terminal `READY`
     (`_decode_dsl("READY…", allow_ready=False)` → None).
3. Run the broader po-agent suite and record failures. Any failure must be shown to be
   **pre-existing** (present before `8903db3`) and not introduced by the 183 owner changes.

---

## Phase 1 — Mandatory 10× DMS-380 multi-step gate (the 182 blocker)
Query: `Покажи DMS-380 и затем задачи его исполнителя`.

1. **Oracle B (fresh, REAL AS21/MCP-SWTR only):**
   - `task.lookup(DMS-380)` → canonical `assignee_login` / `assignee_id`.
   - Canonical source assignee task collection (MCP-SWTR TQL `assigned_to = "<assignee_id>"`)
     → the **parity target count** (do not assume a prior number).
2. **10× gate** (fresh session, concurrency 1): run the query 10×.
   - Each run: turn 2 `task.lookup(DMS-380)` → turn 3 `task.search assignee=<canonical login>`
     → `ready`. Assert the final collection is **exact parity** with Oracle B (same key set /
     same count).
   - **Transport check:** the turn-3 `task.search` → `/api/v1/swtr-read/assignee-tasks`
     read-through must complete within the new bounded policy and **not** fail closed merely
     because the old 30 s ceiling was exceeded. Record per-run latency and whether the
     resilient path (retry/refresh) was exercised.
   - **Bounded-exhaustion check:** confirm the resilient path is bounded (no infinite
     retry) and that a genuine source outage still fails closed (typed
     `source_unavailable`, never an empty/fabricated collection).
3. **Gate result:** `PASS` only if **10/10 exact parity** (with zero wrong `task.lookup`
   recovery, zero recovery-time `READY`, zero fabricated facts).

---

## Phase 2 — Mixed representative generalization matrix (from Assignment 182)
Execute the mixed matrix on the fresh runtime, concurrency 1, comparing every factual
collection against a fresh Oracle B where feasible:
- `3×` person (a single team member, e.g. `Задачи <Full Name>` — exact assignee collection);
- `3×` person + space (`Открытые задачи <Full Name> в <Space>`);
- `3×` PVM-Guru (the representative multi-step / lookup-then-collection pattern);
- `3×` current sprint (`Задачи в текущем спринте <Space>`);
- `2×` lookup-long-desc (a task with a long description, verify bounded observation but exact
  authoritative data);
- `2×` analytical (`sprint.health` / `task.quality` style);
- `2×` unseen (natural phrasings not seen in prior assignments);
- the **three saved defect cases** (re-listed as mandatory in Phase 3 below).

Record per-case status, key count, and parity vs Oracle B. Any non-parity or fail-open
result is a RED signal (attribute to the correct boundary: planner vs capability vs
source/transport vs governance).

---

## Phase 3 — The three previously failing user scenarios (MANDATORY)
These three were the generic capability/governance gaps that 182/181 surfaced. Each MUST
pass now (source-backed and correct), verified against fresh Oracle B:

| # | Query | Expected after 183 fix | Class now covered |
|---|---|---|---|
| 1 | `Открытые задачи Александра Жданова в августовском спринте DMS` | `sprint.search` resolves the "августовский" period to the source-backed canonical sprint (e.g. the August `DMS` sprint); then the member's open tasks in that sprint. COMPLETED with a source-correct count (may legitimately be `0` if the source has none — assert parity, not a specific number). | `sprint.search` (period → sprint) |
| 2 | `Активные спринты в DMS` | `sprint.list` returns the **complete** source-backed active sprint set for `DMS` (e.g. both active `DMS` sprints), NOT a silent singleton. Assert the returned set equals the fresh Oracle B active-sprint set. | `sprint.list` + plural governance |
| 3 | `Покажи открытые задачи Петра Иванова в спринте DMS-SPRNT-2` | `member.resolve` returns the REAL source identity for Ivanov; downstream `task.search` uses the source-backed login and COMPLETES (count may be `0` — assert parity). No `V4ContractError` / roster veto on a valid non-roster source identity. | source-authority identity governance |

**Negative control for case 3 (anti-invention preserved):** a person the source does **not**
resolve (e.g. an invented name with no REAL identity) must still fail closed / clarify —
the 183 identity fix must not have opened an invented-identity path.

**Ambiguity control for case 1:** a period that matches **multiple** source-valid sprints
must return typed ambiguity/clarification, not a silent single choice.

---

## Phase 4 — Safety / governance regression
Source-independent negative probes (all must fail closed with **zero fabricated facts**):
- Invented task (`Покажи DMS-999999`) → "not found", no data.
- Invented person (a name with no REAL identity) → fail-closed / clarify, no data.
- Invented sprint (`... в спринте DMS-SPRNT-999`) → typed clarification / fail-closed.
- Source unavailable (if it occurs) → typed `source_unavailable`, not empty/fabricated.
- Fake `CALL`/`LOAD`/`READY` decode safety (action-only recovery; a bad turn ends in
  `V4ContractError`, fail-closed) — confirm retained.

Also confirm: no local `/api/v1/tasks`/SQLite/frozen/fake fallback was used for any
REAL-backed answer; `semantic_prepass_used=false` throughout.

---

## Phase 5 — Final architecture decision gate
Deliver exactly one verdict:

- **`AGENT_CORE_V4_REPRESENTATIVE_POC_GREEN`** — Phase 0 GREEN, Phase 1 `10/10` exact parity,
  Phase 2 matrix passing (or all discrepancies attributed to pre-existing, non-183 causes
  with evidence), Phase 3 all three scenarios pass with anti-invention preserved, Phase 4
  fail-closed preserved. This re-opens the V4 POC for Browser C / 54-skill migration.
- **`V4_PLANNER_STRATEGY_REVIEW_REQUIRED`** — the owner fixes are correct but a fundamental
  model/control-plane **planner** defect persists (attribute precisely to the planner, with
  the failing turn and trajectory evidence).
- **Bounded RED** — a concrete, bounded, non-planner code/capability/governance defect is
  the blocker; name the exact failing boundary and provide an owner recommendation.
- **`BLOCKED_BY_PROVEN_SOURCE_OUTAGE`** — only if a proven REAL source/transport boundary is
  the **sole** blocker (record the exact failed boundary, the in-isolation success evidence,
  and the owner action). Do not use this if the agent itself is misbehaving.

Rationale for the verdict must cite per-phase evidence (counts, parities, latencies,
trajectories). If the verdict is not GREEN, do **not** recommend proceeding to Browser C /
UI or 54-skill migration.

## Deliverable
- Write the report to:
  `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_REPRESENTATIVE_POC_184.md`
- Include: test base HEAD, owner commits under test, runtime (ports, `agent_core_v4_ready`,
  adapter, source_status), concurrency, Oracle B values (fresh), per-phase results with
  counts/parities/latencies/trajectories, the decision verdict + rationale, and a
  reproduction section (scripts/commands + artifact names).
- Commit and push **only** the QA report:
  ```
  git add -- po-agent-platform-v2/qa_reports/AGENT_CORE_V4_REPRESENTATIVE_POC_184.md
  git commit -m "qa: add AGENT_CORE_V4_REPRESENTATIVE_POC_184.md report"
  git push
  ```

## Final response
Return: report commit SHA, the final verdict, and the complete report contents.

**STOP.** Do not start any further assignment in this run.