# PO Agent V4 — New Chat Handoff
**Date:** 2026-09-24  
**Project:** PO Agent Harness / V4 evolution  
**Branch:** `feat/core8-real-query-hardening-v2`  
**Purpose:** Continue the current V4 migration in a new chat without losing architecture, checkpoints, QA state, or sequencing.

---

## 1. Operating model

The user expects this division of work:

- **ChatGPT / owner**: architecture, production-code changes, migration design, plan/DoD updates, rollback checkpoints.
- **GigaCode**: QA/adversarial testing + service operation only unless the user explicitly changes this rule.
- Detailed GigaCode work goes in `GIGACODE_NEXT_ACTION.md`.
- Commands sent to GigaCode in chat should remain short and standardized.
- Do **not** paste huge assignments into chat unless explicitly asked.

Standard GigaCode command pattern:

> Продолжай работу по ветке `feat/core8-real-query-hardening-v2`.  
> 1. Выполни `git pull --ff-only origin feat/core8-real-query-hardening-v2`.  
> 2. Зафиксируй `START_HEAD`, проверь чистый tracked worktree.  
> 3. Прочитай актуальный `GIGACODE_NEXT_ACTION.md`.  
> 4. Выполни активное задание строго как QA.  
> 5. Production-код не менять и следующее задание самостоятельно не начинать.  
> 6. Commit/push — только QA-отчёт.  
> 7. После завершения остановись и верни verdict + ключевые результаты.

---

## 2. Non-negotiable V4 architecture

V4 is a **single-planner, skill-native, governed Harness**.

### Hard invariant
**Adding a new skill MUST NOT require edits to Agent Core, planner logic, or runtime orchestration business logic.**

Stable extension semantics:

```text
SkillSpec
CapabilitySpec
CapabilityHandler
CompletionContract
UIContract
```

Rules:
- skill discovery/registration is dynamic;
- progressive compact catalog;
- handlers resolved through governed registry;
- procedures live in plugin skill artifacts;
- completion lives in CompletionContract;
- UI shape/widget metadata lives in UIContract;
- new skills are plugin-only;
- no phrase/surname/entity routing;
- no semantic prepass;
- no local/fake/frozen factual truth;
- REAL AS21/MCP-SWTR is authoritative;
- fail closed on missing source;
- no tenant-wide task scan as a substitute for missing source capability;
- source-confirmed identities beat stale local roster;
- recovery may LOAD/CALL but never mint terminal READY;
- exact key-set parity for factual collections where applicable.

The dummy-55 plugin extensibility gate is GREEN and must stay GREEN.

`GVS5H` / multi-agent analytical orchestration is **DEFERRED_TO_V5**. Do not implement it during V4.

---

## 3. Proven rollback checkpoints

Keep these immutable:

```text
A205_GREEN =
checkpoint/v4-a205-green@1fd519105ba6612f535ad98a55cb1302f387ca43

A206B_HISTORY_STATUS_GREEN =
checkpoint/v4-a206b-green@f7f846dee71b676fb0fc8d1d8f0d8aa23d521eaf

WAVE_S1_GREEN =
checkpoint/v4-wave-s1-green@ce64264c868afd73743d5daafdeaee767e07adef

A208B_PRE_S2_GREEN =
checkpoint/v4-a208b-green@2e284fdab79072d95ba0bf86058b4648f4bb9d6c
```

Rollback rule: if a later batch introduces a broad architectural regression that cannot be bounded quickly, return to the latest GREEN checkpoint and re-apply only proven generic fixes.

---

## 4. Important closed defects / lessons

### History/status
Closed:
- nonexistent MCP history tool replaced by real `get_task_history`;
- parser now uses real source fields (`entity.code`, `createdAt`, `user.externalId`);
- no `datetime.now()` substitution for bad source history;
- authoritative custom status labels survive even if generic enum is UNKNOWN;
- `task.time_in_status` stops terminal interval at closure;
- status revisits preserved.

### Person/status
Closed:
- `task.search_assignee` can preserve status constraint;
- `Открытые задачи <человека>` no longer silently returns all tasks;
- raw source status names use `status_raw/status_type`, not enum only.

### Blocked tasks
Closed:
- blocked drill-down uses canonical `task.is_blocked`;
- same predicate as sprint-health blocked count;
- no text/status-name approximation.

### Sprint short forms
Closed:
- S1 metric skills support:
  - explicit sprint id -> `sprint.resolve`;
  - month/period -> `sprint.search`;
  - product-only/current -> `sprint.current`.
- completion contracts were aligned with compacted observations:
  `task_keys -> task_keys_sample + task_key_count`.

---

## 5. Current certified state

### Existing catalog / base runtime
- A205 full existing catalog adversarial: GREEN, zero code RED.
- Browser C representative base scenarios: GREEN.
- local factual `/api/v1/tasks` reads: 0.
- plugin/dummy-55: GREEN.

### Wave S1 — GREEN
Certified:
- `sprint.scope`
- `sprint.velocity`
- `sprint.throughput`
- `sprint.wip`

Manual-query hardening is also GREEN:
- short/current/period forms;
- blocked parity;
- raw source status parity;
- completion-contract compaction.

### Known source-conditional helper
`release.search` is implemented, but live certification is still **SOURCE_CONDITIONAL** because the authoritative release/version directory currently returns HTTP 502.

Observed UI behavior is correctly fail-closed:
`V4 SOURCE_UNAVAILABLE`.

Do **not** replace this with:
- local cache truth;
- broad task scan;
- invented release ids;
- treating `DMS` as a release id.

Re-probe later; source outage is not an S2 code RED.

---

## 6. Current active batch

### A209 / Wave S2 — owner code already implemented, QA pending

Five skills:

1. `sprint.cycle_time`
2. `sprint.lead_time`
3. `sprint.carryover`
4. `sprint.predictability`
5. `sprint.risk_queue`

Owner commits:
- `186c1c6662a493371328d9a188488c12f0e66e66` — five-skill S2 plugin
- `54bfe2932702b17b536ce9a2e71e6dbe7fd62924` — focused S2 tests

Current QA spec:
`GIGACODE_NEXT_ACTION.md`

Current expected verdict:
`AGENT_CORE_V4_WAVE_S2_FIVE_SKILL_GREEN`
or bounded RED / proven source outage.

### Metric semantics

#### cycle_time
Completed tasks only.

```text
terminal workflow transition
-
first workflow-status transition
```

If any completed task lacks required history, fail closed; do not compute a biased partial aggregate.

#### lead_time
Completed tasks only.

```text
terminal workflow transition
-
authoritative task.created_at
```

No `updated_at` or current-time substitution.

#### carryover
Exact key intersection:

```text
previous complete sprint membership
∩
current complete sprint membership
```

If previous sprint is not supplied, resolve predecessor from authoritative sprint dates.

#### predictability
Only when an authoritative committed/baseline scope exists:

```text
completed / committed_baseline
```

Current scope is NOT a valid substitute. Missing baseline => SOURCE_CONDITIONAL/fail-closed.

#### risk_queue
Rank tasks, not people:

1. blocked first;
2. overdue days descending;
3. age days descending;
4. stable task-key tie-break.

Every row must expose reasons/evidence.

---

## 7. Accelerated migration policy

User explicitly wants **larger batches, at least 5 skills**, to finish V4 by the end of September if possible.

Default owner batch from A209 onward: **5 skills minimum when dependencies allow**.

This speeds packaging only; it does not weaken:
- REAL AS21 Oracle;
- Browser C;
- completion contracts;
- plugin invariant;
- fail-closed source behavior;
- local-read audit;
- rollback checkpoints.

### Planned next groups

#### Current: S2 / A209
- cycle_time
- lead_time
- carryover
- predictability
- risk_queue

#### Next batch after A209 GREEN
- `sprint.scope_change`
- `team.workload`
- `team.wip`
- `team.blocked`
- `team.capacity`

#### Following batch
- `team.competency_match`
- `team.assignee_recommendation`
- `team.bottlenecks`
- `team.distribution`
- `release.scope`

#### Following batch
- `release.progress`
- `release.blockers`
- `release.dependencies`
- `release.risk_queue`
- `portfolio.overview`

#### Following batch
- `po.attention_queue`
- `task.search_product`
- `release.forecast`
- `po.daily_brief`
- `po.status_report`

#### Final tail
- `po.reminder_draft`
- `po.local_task_draft`
- any still-uncertified SOURCE_CONDITIONAL skills/helpers
- then full 54-skill A/B/C certification + UI/release hardening

---

## 8. Canonical remaining catalog

### Sprint/flow
- #21 `sprint.health` — already present/GREEN
- #22 `sprint.current` — already present/GREEN
- #23 `sprint.scope` — S1 GREEN
- #24 `sprint.velocity` — S1 GREEN
- #25 `sprint.throughput` — S1 GREEN
- #26 `sprint.wip` — S1 GREEN
- #27 `sprint.cycle_time` — A209
- #28 `sprint.lead_time` — A209
- #29 `sprint.carryover` — A209
- #30 `sprint.scope_change` — next batch
- #31 `sprint.predictability` — A209
- #32 `sprint.risk_queue` — A209

### Team
- #33 `team.workload`
- #34 `team.wip`
- #35 `team.blocked`
- #36 `team.capacity`
- #37 `team.competency_match`
- #38 `team.assignee_recommendation`
- #39 `team.bottlenecks`
- #40 `team.distribution`

### Release/portfolio
- #41 `release.health` — present but source paths remain partly conditional
- #42 `release.scope`
- #43 `release.progress`
- #44 `release.blockers`
- #45 `release.dependencies`
- #46 `release.risk_queue`
- #47 `portfolio.overview`
- #48 `po.attention_queue`

### Reconciled additions
- #49 `task.search_product`
- #50 `release.forecast`
- #51 `po.daily_brief`
- #52 `po.status_report`
- #53 `po.reminder_draft` — draft only
- #54 `po.local_task_draft` — draft only

---

## 9. Required QA gate for every batch

GigaCode independently verifies:

1. plugin-only architecture/static gate;
2. focused unit/contract tests;
3. fresh REAL AS21 Oracle immediately before factual live tests;
4. exact key/fact parity;
5. no local factual source;
6. no broad task-scan fallback;
7. Browser C representative scenarios;
8. negative/no-match/ambiguous/source-unavailable states;
9. retained high-risk regression;
10. dummy-55/plugin invariant;
11. immutable checkpoint after GREEN.

A SOURCE_CONDITIONAL skill may remain conditional without making unrelated source-backed skills RED, but only if source absence/outage is independently proven and behavior is fail-closed.

---

## 10. Endgame / release readiness

After all 54 skills are terminally classified:

- full 54-skill Agent A / REAL Oracle B / Browser C;
- full UI/widget E2E;
- re-probe all SOURCE_CONDITIONAL cases;
- rollback rehearsal;
- P0 defects = 0;
- unauthorized writes = 0;
- secret leakage = 0;
- release hardening;
- then and only then:
  `RELEASE_READY=YES`.

V5 multi-agent work starts only after V4 completion.

---

## 11. Files to read first in a new chat

Read these before making new implementation decisions:

1. `PO_AGENT_HARNESS_EVOLUTION_PLAN.md` — especially §14–15.
2. `V4_DOD_LOCK.md`.
3. `V4_54_SKILL_MIGRATION_PLAN.md`.
4. `GIGACODE_NEXT_ACTION.md`.
5. Latest QA report for the active assignment.
6. Active plugin file(s), currently:
   `po-agent-platform-v2/src/po_agent/harness/v4_plugins/wave_s2.py`.

---

## 12. Immediate next action

**Do not implement the next batch yet.**

Current action:

```text
WAIT_FOR_A209_RESULT
```

When A209 returns:

### If GREEN
1. inspect the QA report;
2. freeze a new immutable Wave S2 checkpoint;
3. update plan/DoD current state;
4. owner-implement the next 5-skill batch:
   `sprint.scope_change + team.workload + team.wip + team.blocked + team.capacity`;
5. create the next QA assignment in `GIGACODE_NEXT_ACTION.md`.

### If RED
1. classify exact first defect: code / architecture / source / planner / contract / UI;
2. owner makes the smallest generic fix;
3. GigaCode re-gates;
4. do not start next batch until GREEN or proven SOURCE_CONDITIONAL.

### If BLOCKED_BY_PROVEN_SOURCE_OUTAGE
Do not "fix" code to bypass the source. Re-probe later and continue only when the active batch can be certified honestly.

---

## 13. Communication preference

The user wants:
- Russian responses;
- concise, direct, practical;
- clear next step;
- no architecture drift;
- checkpoints before risky transitions;
- larger skill batches (>=5) to accelerate delivery;
- no moving forward while a real code RED remains.

When giving GigaCode a command, keep it short and point it to `GIGACODE_NEXT_ACTION.md`.
