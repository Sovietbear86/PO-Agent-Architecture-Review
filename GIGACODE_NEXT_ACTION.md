# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_186_V4_REPRESENTATIVE_POC_REGATE`

## Role
**QA / tester only.** Do NOT edit production code, prompts, adapters, tests,
config, or AS21/SWTR data. Do NOT run a full tenant-wide task sync. Do NOT commit
`.env`, credentials, or secrets. You may run tests, collect a fresh REAL Oracle
B, run the live agent, and commit/push only the allowed QA report file.

## Mission
Re-gate the V4 representative POC after the Assignment 185 bounded
source-correctness hardening. Assignment 185 fixed the two pre-existing
non-planner defects that held Assignment 184 at `V4_BOUNDED_RED`:

- **B1** — REAL sprint-task collection for >100-task sprints (the live MCP
  `get_sprint_tasks` has no page input; the old loop amplified one 100-row page
  into ~10,000 duplicates and failed closed at 3×90 s). Now: canonical
  `unit.code` identity, zero-new-page stop, source-backed TQL fallback, typed
  `complete=false`, and the production adapter fails closed on incomplete.
- **B2** — terminal/open status classification for opaque encoded workflow keys
  (`CNCLLD_…`, `PN_…`, `CLSD_…`). Now: the assignee route emits the decoded
  `workflow_status` (name + `statusType`) in the flat `swtr_attributes`
  contract, the agent `_attributes` parser is tolerant of both encodings, and
  `Task.is_open`/`is_completed` are driven by the source's authoritative
  `statusType` category (terminal vs non-terminal), with undecodable statuses
  explicitly neither open nor completed.

Assignment 185 owner verification (confidence only, not certification) already
showed, against fresh REAL AS21 through the production adapter
(`EvidenceValidatedProductionTaskApiAS21Adapter`):
- B1: DMS-SPRNT-1 → **104/104** exact key parity vs fresh TQL (~3 s, no timeout);
  DMS-SPRNT-2 → 39/39.
- B2: Kalachanov.V.V assignee → 2858 rows, **open=490 / terminal=2368 /
  undecodable=0**, exactly matching the source-fact `statusType` ground truth.
- Retained smoke: DMS-380 (QA / progress / open, space DMS, sprint DMS-SPRNT-2);
  invented identity → fail-closed (`AS21SourceUnavailable`, zero fabrication).

Your job: independently re-run the full gate against a **fresh** REAL AS21
Oracle, confirm B1/B2 hold, confirm the previously-fixed scenarios and safety
invariants are retained, and return exactly one final verdict. **Stop after the
report.**

## Mandatory pre-read
```bash
git pull --ff-only origin feat/core8-real-query-hardening-v2
```
Then read:
- `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_REPRESENTATIVE_POC_184.md` (the
  prior gate, baseline failure set, and Oracle B method)
- `po-agent-platform-v2/docs/v4_dod/V4_DOD_LOCK.md`
- `GIGACODE.md` (A182/A184 memories: environment, transport budget, Oracle facts)
- The two Assignment 185 commits for the exact fix surface:
  - B1: `git show e997e3a --stat` (task-api `swtr_read.py`, adapter
    `production_task_api.py`, `test_swtr_read_sprint_collection.py`,
    `test_sprint_collection_b1.py`)
  - B2: `git show cc39e18 --stat` (models.py, `task_api.py`,
    `hardened_production_task_api.py`, `agent_core_v4.py`, task-api
    `swtr_assignee.py`, `test_status_semantics_b2.py`,
    `test_swtr_assignee_canonical.py`)

## Environment
- Branch: `feat/core8-real-query-hardening-v2` (record `START_HEAD = git rev-parse HEAD`).
- Python: `po-agent-platform-v2/.venv/bin/python` (agent + tests); global
  `python3` (task-api).
- Task API: SSE to MCP-SWTR `http://127.0.0.1:3000/sse`. Resilient transport
  budget is 90 s × 3 on read-through routes. Use **fresh** task-api + agent
  instances on **free** ports (stale agents from prior runs are common — probe
  `/health` and prefer a fresh port). A fresh task-api needs no token in SSE
  mode (the running MCP-SWTR is already authenticated).
- Blocked operations (per tooling): `curl`, `ps aux`, `lsof`, process `kill`,
  reading `.env`, `$()` / `<(...)` command substitution. Use the Python venv
  `httpx` for HTTP diagnostics.

## Known pre-existing failures (NOT regressions)
The A184 baseline failure set is **16 failed + 11 errors** (real-LLM integration
env, SWTR live-integration, and order-dependent isolation cases such as
`test_skill_registry::test_get_active_skills`). A185 added 15 po-agent tests and
introduced **zero** new failures (1349 passed = 1334 + 15). Any failure you see
must be cross-checked against the A184 report's 27-node set; a byte-identical
set (plus the new passing tests) = no regression. A *new* node ID = report it.

---

## Phase 1 — Fresh build / protocol / static gate

1. `git pull --ff-only`, record `START_HEAD`.
2. Run the focused B1/B2 regression suites (all must be GREEN):
   ```bash
   # task-api
   cd task-api && python3 -m pytest \
     tests/test_swtr_read_sprint_collection.py \
     tests/test_swtr_assignee_canonical.py \
     tests/test_swtr_read_facade.py -q
   # po-agent
   cd po-agent-platform-v2 && .venv/bin/python -m pytest \
     tests/test_sprint_collection_b1.py \
     tests/test_status_semantics_b2.py -q
   ```
3. Broader po-agent suite — compare the FAILED/ERROR node-ID set to the A184
   27-node baseline. **No new node ID is acceptable.**
   ```bash
   cd po-agent-platform-v2 && .venv/bin/python -m pytest -q
   ```
4. task-api swtr suite (guard the `swtr_assignee.py` change):
   ```bash
   cd task-api && python3 -m pytest \
     tests/test_swtr_read_facade.py tests/test_swtr_read_sprint_collection.py \
     tests/test_swtr_assignee_canonical.py tests/test_swtr_health_guard.py \
     tests/test_swtr_mcp_client.py tests/test_task_api_freshness.py -q
   ```
5. Static invariants (all must hold):
   - No semantic prepass on the V4 path (no `prepass(` call-site; all
     `semantic_prepass_used` emissions `false`).
   - No surname/entity/space/task-code/sprint-id hardcode introduced in the
     owner-changed production files (executable code, not docstrings/comments).
   - No planner/model/prompt-strategy change (model/provider still
     `Qwen/Qwen3.8-27B`).
   - Action-only recovery / fail-closed behavior unchanged.

**GATE 1:** all focused suites GREEN + no new broader failure node + all static
invariants hold. Any failure → bounded RED (stop and report the exact boundary).

## Phase 2 — Fresh REAL Oracle B (collect live; hardcode nothing)

Against a fresh task-api (SSE to MCP-SWTR), collect and record, all source-backed:
- **B1:** a REAL sprint with >100 tasks (DMS current sprint is acceptable if
  still source-valid) — the true complete key set via the source-backed TQL
  sprint-constraint query (pageable), plus a smaller sprint for the singleton
  case. Record the exact key sets.
- **B2:** a REAL assignee+space collection containing encoded workflow statuses
  (STS is acceptable if still source-valid) — for every row, the authoritative
  `statusType` (from the decoded `workflow_status`), and the resulting
  non-terminal (open) vs terminal split. Record the exact open/terminal key sets.
- **Retained:** DMS-380 single-task facts (space, sprint, status name/type,
  assignee); the DMS active-sprint set; the August-2026 DMS sprint resolution;
  a valid non-roster REAL identity (e.g. Пётр Иванов if still source-valid);
  a few assignee collections for the mixed matrix (e.g. Semavin, Zhdanov,
  Kalachanov) with their exact task counts and open/terminal splits.
- Confirm `PVM-Guru` is (still) not a source entity (A184 finding).

Save Oracle artifacts under the repo root as `qa_186_oracle_*` (untracked is
fine unless intended as a durable fixture).

## Phase 3 — B1 regression family (exact key parity)

Through the **production** source path (route and/or
`EvidenceValidatedProductionTaskApiAS21Adapter`):
- The >100-task sprint returns the **complete exact task-key set** == fresh
  Oracle B (no missing, no extra).
- No duplicate-page amplification (unique == total; no 10,000-row blowup).
- No 3×90 s timeout pattern; bounded latency.
- The small sprint returns its exact complete set (no singleton loss).
- Natural query `Задачи в текущем спринте DMS` (or equivalent source-valid
  current-sprint query) completes with exact parity.

## Phase 4 — B2 regression family (exact key parity)

Through the **production** source path:
- For the encoded-status assignee+space collection, the production adapter maps
  `statusType` correctly; `not_completed`/open returns the **exact non-terminal
  key set** (not merely the same count) == fresh Oracle B.
- Terminal keys are excluded; undecodable keys are excluded from "open"
  (never silently inflated).
- Human-readable statuses (product spaces already correct) are unchanged.
- Natural `Открытые задачи <person> в <space>` returns the exact non-terminal set.

## Phase 5 — Retained scenarios (from A183/A184)

Each must still pass against fresh source:
1. **10× DMS-380 benchmark** — `Покажи DMS-380 и затем задачи его исполнителя`
   → exact source-backed completion, 10/10.
2. **Three previously-fixed user scenarios** (A183):
   - `Открытые задачи Александра Жданова в августовском спринте DMS` (source-backed
     period resolution via `sprint.search`);
   - `Активные спринты в DMS` (complete active set, no singleton loss, via
     `sprint.list`);
   - source-authority identity (no stale local-roster veto).
3. Valid non-roster REAL identity (e.g. Пётр Иванов) — no roster veto.
4. Invented identity — **fail closed** (zero fabricated tasks).

## Phase 6 — Mixed representative matrix + unseen combinations

A matrix across people × spaces × sprints × status (including unseen
combinations not used in A183/A184/A185), each with exact source-backed
parity. Include at least one >100-task sprint and at least one encoded-status
STS collection in the mix.

## Phase 7 — Safety / governance / fail-closed

- Invented task / person / sprint → fail closed, zero fabrication.
- Source outage (optional dead-source probe) → typed fail-closed, not empty.
- No empty/fabricated "complete" sprint (B1 typed `complete=false` respected).
- No semantic prepass; action-only recovery intact.

---

## Final verdict (exactly ONE)
- `AGENT_CORE_V4_REPRESENTATIVE_POC_GREEN` — all gates green, B1/B2 exact
  parity live, retained scenarios + safety intact.
- `V4_PLANNER_STRATEGY_REVIEW_REQUIRED` — a planner/model/protocol (not
  source-correctness) issue is the binding boundary.
- A **bounded RED** with the exact first-failing boundary (name the node,
  the query, the expected vs observed, and the source fact).
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE` — a proven, reproducible REAL source
  outage blocks the mandatory gate (not a code defect).

**If GREEN:** include an explicit recommendation to **STOP backend POC
remediation and proceed to Browser C/UI**, then the **progressive 54-skill
catalog migration**.

## Deliverable
Write the report to:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_REPRESENTATIVE_POC_REGATE_186.md`

Include: START_HEAD, Oracle B facts (fresh), per-phase results with exact
counts/keys, the failure-set comparison to A184, static-invariant results, and
the single final verdict (+ GREEN recommendation if applicable).

## Commit discipline
Commit **only** the allowed report file:
```bash
git add -- po-agent-platform-v2/qa_reports/AGENT_CORE_V4_REPRESENTATIVE_POC_REGATE_186.md
git commit -m "qa: add AGENT_CORE_V4_REPRESENTATIVE_POC_REGATE_186.md report"
git push
```
Keep QA scratch artifacts untracked unless intended as durable fixtures.

## Completion criteria for Assignment 186
Assignment 186 is complete only when:
- the fresh build/protocol/static gate is green (or a bounded RED boundary is named);
- the fresh REAL Oracle B is collected and cited (nothing hardcoded);
- B1 and B2 exact key parity is proven live;
- the 10× DMS-380 benchmark and the three previously-fixed scenarios are retained;
- the mixed matrix + unseen combinations pass;
- safety/governance/fail-closed checks pass;
- exactly one final verdict is returned (with the GREEN recommendation if GREEN);
- the report is committed and pushed;
- then **STOP**. Do not start any further assignment in the same session.