# GigaCode — Current Action

## Status
`ACTIVE_OWNER_ASSIGNMENT_183_V4_SOURCE_AND_CAPABILITY_HARDENING`

## Mission
Continue Agent Core v4 from the completed Assignment 182 checkpoint. **Do not restart the V4 POC.**

Assignment 182 established two important facts:
1. the planner observation-hygiene fix is correct — on the critical DMS-380 turn the planner chose the correct `task.search assignee=semavin.m.m` in 30/30 runs and the former long-description derailment disappeared;
2. the representative POC decision gate could not be completed because the long-lived runtime repeatedly hit a source/transport boundary on `task.search -> /api/v1/swtr-read/assignee-tasks` with the current 30 s client timeout, while the same REAL-AS21 operation succeeded with fresh connections.

In addition, three live user scenarios exposed **generic capability/governance gaps**, not DMS-380-specific planner defects:
- `Открытые задачи Александра Жданова в августовском спринте DMS` — no generic period/date -> sprint resolution/search capability;
- `Активные спринты в DMS` — `sprint.current` silently returns a singleton for a plural/list request; no sprint list/search capability;
- `Покажи открытые задачи Петра Иванова в спринте DMS-SPRNT-2` — REAL source identity resolution can succeed but downstream local roster/literal governance can still reject the source-backed person.

This assignment is a **bounded owner hardening pass across source transport + missing generic sprint capabilities + source-authority governance**. It is NOT permission for phrase/entity-specific routing, DMS-380 special cases, person-specific fixes, prompt hacks or another planner-model micro-patch.

After the owner changes are complete and covered by focused tests, create a new QA assignment in `GIGACODE_NEXT_ACTION.md` to re-run the blocked Assignment 182 decision gate. Do **not** declare the POC GREEN in this owner assignment.

## Absolute rules
- First: `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
- Read `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_FINAL_POC_DECISION_182.md` before editing.
- Preserve the current Qwen/provider and V4 raw-query/progressive-skill architecture.
- REAL AS21 remains authoritative. Do not introduce local `/api/v1/tasks`, SQLite, frozen/fake data or hardcoded entity truth as a fallback.
- Do not reintroduce semantic pre-pass routing, surname rules, phrase routers, entity-specific branches or trajectory hardcodes.
- Do not weaken fail-closed behavior. Source timeout/unavailability must never become a fabricated empty collection.
- Do not change acceptance thresholds in the future QA gate.
- Production changes must be generalized and have focused regression tests.
- Keep V3/H1B rollback checkpoint untouched.

---

## Phase 1 — Fix the proven `assignee-tasks` source/transport reliability boundary

### Problem to solve
Assignment 182 showed:
- direct/fresh REAL calls for the Semavin assignee collection succeed and return the complete collection;
- the long-lived PO Agent runtime repeatedly fails on the same `task.search -> /api/v1/swtr-read/assignee-tasks` path because the adapter currently has a 30 s HTTP ceiling and the live paged read-through can exceed it under sequential load;
- the planner decision at this boundary is correct, so do not change planner logic to hide the transport failure.

### Required implementation properties
Implement a generalized production transport hardening for REAL read-through calls. The solution may use the smallest appropriate combination of:
- operation-aware/source-read timeout greater than the current 30 s ceiling;
- bounded retry with backoff for transient timeout/connection failures;
- connection/client refresh when a pooled long-lived connection becomes unhealthy;
- equivalent generic transport resilience already consistent with the adapter architecture.

Requirements:
1. no infinite retry;
2. no retry storm;
3. no fake/local fallback;
4. source-unavailable after bounded retries remains typed/fail-closed;
5. ordinary fast operations must not become needlessly slow;
6. the policy must be generic — not keyed to `semavin.m.m`, DMS-380, one endpoint, or one task count unless an operation class legitimately requires a larger source-read budget;
7. preserve exact source results and evidence.

Add focused tests for timeout/retry/connection behavior, including exhaustion -> typed source-unavailable.

---

## Phase 2 — Add generic sprint discovery/list capabilities

The current V4 catalog can resolve a known sprint id and return one current sprint, but it cannot reliably answer natural requests that require sprint discovery or a collection of sprints.

Implement the smallest reusable capability surface needed for both of these classes:

### A. Sprint search / period resolution
Support queries such as:
`Открытые задачи Александра Жданова в августовском спринте DMS`

The agent must be able to convert a human temporal reference (month/date/period such as `августовский спринт`) into source-backed candidate sprint(s), then bind the selected canonical sprint id into the downstream task search.

Preferred architecture: a generic `sprint.search` / `sprint.find_by_period`-style capability backed by REAL AS21 sprint/task source data.

Do not encode Russian month names or this exact phrase as a routing special case in production. Temporal interpretation may normalize a user-provided date/month/period, but the resulting sprint identity must be proven from source data.

If multiple source-valid sprints match the requested period, return typed ambiguity/clarification instead of silently choosing one.

### B. Sprint list/search
Support plural/list requests such as:
`Активные спринты в DMS`

Add a generic source-backed sprint collection capability (`sprint.list`, `sprint.search`, or equivalent) that can return all matching active/currently relevant sprints in a product space.

**Critical governance invariant:** a singleton capability such as `sprint.current` must not silently satisfy a request for a collection when source data contains multiple matching sprints.

A successful answer that drops the plurality constraint is a defect (`silent constraint loss`), even if the returned sprint itself is valid.

Add focused tests for:
- one matching sprint;
- multiple matching sprints;
- zero matching sprints;
- period match;
- ambiguous period match;
- plural request cannot be completed through `sprint.current` alone when that would be incomplete.

---

## Phase 3 — Make REAL source-backed identity authoritative over stale local roster guards

Reproduce:
`Покажи открытые задачи Петра Иванова в спринте DMS-SPRNT-2`

Assignment 182 evidence indicates REAL `/assignees/resolve` can return a source identity, yet downstream V4 validation can reject it because the user/person literal is not present in the local team roster / query-derived guard path.

Fix the generalized governance rule:
- an identity that was successfully resolved and returned by the governed REAL `member.resolve` observation is trusted as source-backed identity for subsequent governed calls;
- downstream calls should use an observation reference to the canonical source identity;
- local roster may remain useful as a non-production/fake fallback, but it must not veto an unambiguous REAL-AS21 identity already established by `member.resolve`;
- planner still may not invent arbitrary logins or ids.

Do not special-case `Петр Иванов`, any surname, or any team-member list.

Add focused tests proving:
1. a person absent from the local roster but uniquely resolved by REAL/source-backed `member.resolve` can flow into `task.search`;
2. unresolved/ambiguous person still fails closed / clarifies;
3. invented planner identity without a source observation is still rejected.

---

## Phase 4 — Focused integration validation

After implementation, run focused unit/integration tests and then re-run each previously failing class against the freshest available REAL source, concurrency 1:

1. source transport probe for an assignee collection large enough to exercise the live read-through;
2. `Открытые задачи Александра Жданова в августовском спринте DMS`;
3. `Активные спринты в DMS`;
4. `Покажи открытые задачи Петра Иванова в спринте DMS-SPRNT-2`.

For every factual collection, compare against a direct REAL-AS21 Oracle B where feasible.

Do not hardcode expected counts from previous runs. Refresh them from the source.

Acceptance for this owner assignment:
- transport call no longer fails merely because the previous 30 s ceiling is exceeded within the new bounded reliability policy;
- bounded exhaustion still fails closed;
- temporal sprint query reaches a source-backed canonical sprint or typed ambiguity;
- plural active-sprint query returns the complete source-backed matching sprint set, not a silent singleton;
- REAL-resolved non-roster identity can be used downstream without weakening anti-invention safeguards;
- no new surname/phrase/entity/trajectory hardcodes;
- focused regression suite GREEN.

If a requested capability cannot be implemented from available REAL AS21 data/contracts, document the exact source limitation instead of fabricating semantics.

---

## Phase 5 — Commit discipline

Production/test changes are allowed in Assignment 183 because this is an owner remediation assignment.

Commit logically grouped generalized changes. Suggested grouping:
1. source transport reliability;
2. sprint discovery/list capability + governance;
3. source-backed member identity trust;
4. tests/docs as needed.

Do not modify the Assignment 182 QA report except to leave it as historical evidence.

---

## Phase 6 — Prepare the next QA gate, then STOP

When all owner changes and focused tests are complete:

1. update `GIGACODE_NEXT_ACTION.md` again with a **QA-only Assignment 184** that re-runs the blocked representative POC decision gate;
2. Assignment 184 must include:
   - fresh 10× `Покажи DMS-380 и затем задачи его исполнителя` exact Oracle parity;
   - mixed representative gate from Assignment 182;
   - the three regression scenarios above as mandatory cases;
   - safety/governance checks;
   - no production edits during QA;
   - final architecture verdict (`AGENT_CORE_V4_REPRESENTATIVE_POC_GREEN` vs planner/architecture review vs bounded source/adapter RED).
3. commit/push the owner changes and the new `GIGACODE_NEXT_ACTION.md`.
4. STOP. Do not execute Assignment 184 yourself in the same run.

## Final response
Return a concise summary containing:
- commits created;
- exact production areas changed;
- focused test results;
- live re-check result for each of the four classes;
- confirmation that `GIGACODE_NEXT_ACTION.md` now contains Assignment 184 QA instructions;
- any remaining proven blocker.