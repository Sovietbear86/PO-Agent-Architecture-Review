# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_195D_V4_UNIVERSAL_IDENTITY_RESOLVER_REGATE`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT implement, refactor, fix, improve, or rewrite production code, frontend code, plugin code, tests, prompts, adapters, config, or architecture docs. Do not start Wave S until this gate is GREEN.

## Why 195C is superseded
A195B correctly found the morphology grounding defect, and the owner implemented its generic fix. Before 195C was run, manual Browser-C testing exposed a broader regression in `task.search_assignee`:

- team member natural references can still collapse into generic `FAILED` instead of clarification/resolution;
- a real person outside the configured PO-agent team must be searchable, but the A194/A195 fast path made the local team directory too influential;
- ambiguous/not-found identities are surfacing as generic `AS21 returned invalid data` instead of typed `NEEDS_CLARIFICATION` / safe not-found behavior.

The owner traced this regression to commit `7cfbc5e` (`fix(v4): source-backed assignee hint without core edits`). That optimization changed `task.search_assignee` from the generic governed person-resolution contract to:

`team hint if unique -> otherwise raw reference -> search_tasks`

This worked for the narrow A195 cases but bypassed the previously proven generic `member.resolve` behavior for arbitrary AS21 users.

## Owner fix under test
Current owner fix restores the universal contract **inside the task plugin handler, without adding per-person or per-skill logic to Agent Core**:

`task.search_assignee -> generic member.resolve -> canonical REAL AS21 identity -> live assignee task route`

Properties that MUST hold:
1. The configured team directory is an optional disambiguation/performance hint only. It is **not** the searchable population and may never veto a valid REAL AS21 identity.
2. A person outside the local team can be resolved and queried if REAL AS21 can identify them.
3. A team member and a non-team person go through the same governed identity contract.
4. Ambiguous source identities produce `NEEDS_CLARIFICATION` with useful candidate/login options when available; they must not become generic source corruption errors.
5. Unknown identities fail closed with a user-understandable clarification/not-found result, not fabricated zero tasks and not `AS21 invalid data` unless the source payload is genuinely malformed.
6. Morphological normalization from A195B remains supported.
7. REAL AS21 remains authoritative. No local `/api/v1/tasks`, SQLite, roster-only truth, or fake/snapshot fallback.
8. Hermes/plugin invariant remains intact: no person-specific production hardcodes; no new Agent Core/planner/completion changes for this identity behavior.

Owner commits after A195B:
- `043823f7b7671b145fd8a49758f4d02ba9737fcb` — generic morphology grounding seam;
- `e0fe3139b03e3d52f42f21d4f095426b36cbbd11` — morphology regression tests;
- `ab71a8c4769a998ed5bcad6d709a0a75337da43a` — restore universal source-backed assignee resolution in plugin handler;
- `f6e44ad0b883915b78c29a47923afa330eaad434` — focused universal resolver contract tests.

Permanent rollback remains `0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`.

## Mission
Independently prove or reject that person resolution is again generic, source-authoritative, morphology-safe, clarification-safe and **not limited to configured team members**.

## Phase 0 — start / architecture audit
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record exact `START_HEAD`; tracked worktree must be clean.
3. Read A195B report, A195 report, `V4_DOD_LOCK.md`, `V4_54_SKILL_MIGRATION_PLAN.md` and owner diff since `749e993d04dfe3f741eaf7f38afc02135869d858`.
4. Confirm the assignee behavior change is in plugin/source boundary only. No new person-name hardcodes, surname routers, semantic-prepass, Agent Core skill branches, planner strategy changes, completion changes, or local-store fallback.
5. Confirm `task.search_assignee` invokes the generic governed member resolver before factual task collection.
6. Confirm the local team directory is only a hint inside resolution and cannot define/limit the AS21 person population.

Any violation => RED. Do not fix it.

## Phase 1 — focused tests
Run at minimum:

```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_v4_owner_fix_contracts.py -v
python -m pytest tests/test_v4_pluginized_morphology_grounding.py -v
python -m pytest tests/test_agent_core_v4_reliable.py -v
python -m pytest tests/test_agent_core_v4_plugin_registry.py -v
python -m pytest tests/ -k "v4 and (assignee or identity or ground or plugin or reliable)" -v
```

No code/test edits.

## Phase 2 — fresh REAL AS21 identity Oracle B
Use source routes directly; Agent output is never Oracle B.

Build independent Oracle B for these identity classes:

### A. Configured team members
At minimum:
- Александр Жданов / `Zhdanov.A.Ni`;
- Родион Гаранин / `Garanin.R.V`;
- Агатаева (use the actual configured team entry and canonical login from current config/source; do not guess the login).

For each, prove the canonical REAL AS21 identity and, where practical, exact current task key set in one known space.

### B. Real non-team person
Use **Уткин** as the primary user-provided case. First establish from REAL AS21 whether the surname maps to:
- exactly one person;
- multiple people;
- or requires fuller text/login.

Do not treat local team configuration as authority. If `Уткин` is ambiguous, capture the real source candidates and use one source-proven full name/login as the unique follow-up control.

### C. Unknown identity
Use one clearly invented person and prove how the source resolver responds.

## Phase 3 — API identity matrix through public `/api/v1/query`
Fresh sessions, concurrency 1.

Run at minimum:

### Team + morphology
- `Задачи Александра Жданова в DMS`
- `Задачи Родиона Гаранина в DMS`
- `Задачи Жданова в DMS`
- `Задачи Гаранина в DMS`
- `Задачи Агатаевой`
- natural full-name/case variant for the configured Агатаева entry (derive exact first name from config/source, not memory)

### Non-team
- `Задачи Уткина`
- if ambiguous: select/provide one returned full identity/login and rerun the task query;
- if unique: require exact task-key parity with Oracle B.

### Unknown / negative
- `Задачи Пупкина` or another invented identity verified absent from source;
- one deliberately ambiguous real surname if available from Oracle B.

For every case capture:
- response status;
- loaded skill;
- person `reference` emitted by planner;
- resolver call/result and canonical login/external id;
- clarification id/options when applicable;
- task collection call only after canonical identity is source-confirmed;
- exact task-key parity for factual completions;
- `semantic_prepass_used=false`;
- no local task-store read.

### Mandatory semantics
- Unique REAL identity -> `COMPLETED` with exact source-backed tasks.
- Ambiguous REAL identity -> `NEEDS_CLARIFICATION`, useful candidates when source exposes them; **never generic `FAILED: AS21 invalid data`**.
- Unknown identity -> typed clarification/not-found/fail-closed; **never fabricated zero-as-fact and never source-corruption text unless payload is actually malformed**.

## Phase 4 — source/route provenance
For one team member and one non-team member prove the route conceptually and from logs:

`task.search_assignee plugin -> generic member.resolve -> REAL AS21 identity resolver -> canonical identity -> live assignee task query -> MCP-SWTR -> REAL AS21`

Team-directory participation, when present, must be recorded only as a hint. Repeat a non-team case where no roster entry exists to prove the route still works/clarifies entirely from REAL AS21.

No `/api/v1/tasks`, SQLite, local snapshot, fake or frozen fallback is allowed.

## Phase 5 — Browser C adversarial matrix
Use the actual UI. At minimum run:
- `Задачи Александра Жданова в DMS`
- `Задачи Родиона Гаранина в DMS`
- `Задачи Агатаевой`
- `Задачи Уткина`
- one invented person

Requirements:
- successful identities render factual V4 results;
- ambiguity renders an actual clarification interaction, not a red generic error panel;
- clarification choice/manual reply preserves context through the existing continuation mechanism;
- unknown identity presents a meaningful safe result;
- no stale `AS21 вернул некорректные данные` for ordinary ambiguity/not-found cases.

Capture request/response/status/widget/evidence/clarification payloads.

## Phase 6 — retained regression
Run once each:
- `Покажи DMS-380 и затем задачи его исполнителя` exact Oracle parity;
- `Покажи открытые задачи в DMS` exact parity;
- WMB-30000 attachment lookup exact live parity;
- sprint clarification continuation once;
- plugin/dummy-55 structural gate.

No full 20-row Task Wave rerun unless a retained case fails.

## Phase 7 — service keepalive
After QA, leave the current-HEAD UI/backend/Task API running and return frontend/backend/Task API URLs, ports, PIDs, health and exact START_HEAD.

## Allowed output
Create/commit/push **only**:

`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_UNIVERSAL_IDENTITY_RESOLVER_REGATE_195D.md`

## Verdict
Use exactly one:
- `AGENT_CORE_V4_TASK_WAVE_GREEN`
- `AGENT_CORE_V4_TASK_WAVE_REOPENED_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires all of the following:
- A195B morphology full-name failures fixed;
- configured team members work through generic source-backed identity resolution;
- at least one source-proven **non-team** identity works or, when surname is genuinely ambiguous, produces correct clarification followed by successful unique follow-up;
- ambiguity/not-found never collapses into generic source-corruption messaging;
- anti-invention and live-only invariants remain GREEN;
- no retained regression;
- Hermes/plugin extensibility intact.

If GREEN, recommendation must be:
**Re-close Wave T (#1-20) and proceed to owner Wave S (#21-32 Sprint/flow) through the existing plugin surface.**

## STOP
After committing/pushing only the QA report and leaving current-HEAD services running, stop and wait for the owner.