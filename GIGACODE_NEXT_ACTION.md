# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_195C_V4_ASSIGNEE_MORPHOLOGY_FIX_REGATE`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT implement, refactor, fix, improve, or rewrite production code, frontend code, plugin code, tests, prompts, adapters, config, or architecture docs. Do not start Wave S until this re-gate is GREEN.

## Context
A195B reproduced a deterministic user-visible morphology defect:
- `Задачи Александра Жданова в DMS` -> FAILED;
- `Покажи задачи Александру Жданову в DMS` -> FAILED;
- same class for `Родион Гаранин`;
- surname-only and nominative full-name controls succeed.

A195B localized the defect to generic grounding: plugin capabilities expose a natural human argument named `reference`, but the reliable base runtime applied morphology-aware validation only to `member.resolve.reference`. Other `reference` arguments were incorrectly revalidated by literal-substring grounding before the source-backed handler could run.

The owner has now implemented a minimal generic fix in the **pluginized production overlay**, not in per-skill routing:
- every non-observation `reference` first passes the existing conservative `_reference_is_safe_normalization` person-grounding check;
- after that, only the `reference` key is removed before delegating to the certified base literal guard, so `space`, `sprint_id`, `release_id`, `task_key`, `product`, trusted `assignee`, etc. retain their previous safety checks;
- REAL AS21 remains authoritative downstream; the team directory is still only a hint;
- no person/surname-specific production rule was added;
- no planner/model/completion/source strategy change was made.

Owner commits after A195B report:
- `043823f7b7671b145fd8a49758f4d02ba9737fcb` — generic pluginized morphology grounding fix;
- `e0fe3139b03e3d52f42f21d4f095426b36cbbd11` — focused regression tests.

Permanent rollback remains `0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`.

## Mission
Independently prove or reject that the A195B morphology defect is fixed **without weakening anti-invention or breaking Hermes/plugin extensibility**.

## Phase 0 — start / architecture audit
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record `git rev-parse HEAD` as `START_HEAD`; tracked worktree must be clean.
3. Read A195B report and owner diff since `749e993d04dfe3f741eaf7f38afc02135869d858`.
4. Confirm production changes are limited to the generic pluginized runtime seam; no new person-specific hardcode, planner strategy changes, completion changes, local-store fallback, or per-skill Agent Core routing.
5. Confirm another plugin capability using natural human `reference` can inherit this behavior without an Agent Core edit.

Any violation => RED. Do not fix it.

## Phase 1 — focused tests
Run at minimum:

```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_v4_pluginized_morphology_grounding.py -v
python -m pytest tests/test_agent_core_v4_reliable.py -v
python -m pytest tests/test_agent_core_v4_plugin_registry.py -v
python -m pytest tests/test_v4_owner_fix_contracts.py -v
python -m pytest tests/ -k "v4 and (ground or plugin or reliable)" -v
```

No code/test edits.

## Phase 2 — fresh REAL AS21 morphology matrix
Use fresh sessions, concurrency 1, public `/api/v1/query`, REAL AS21 Oracle B.

Run exactly:
- `Задачи Александра Жданова в DMS`
- `Задачи Жданова в DMS`
- `Покажи задачи Александру Жданову в DMS`
- `Что делает Александр Жданов в DMS`
- canonical-login control for the same person
- `Задачи Родиона Гаранина в DMS`
- `Задачи Гаранина в DMS`
- `Покажи задачи Родиону Гаранину в DMS`
- `Что делает Родион Гаранин в DMS`
- canonical-login control for the same person

For every successful factual case require:
- dedicated `task.search_assignee` skill;
- source-backed identity confirmation;
- exact task-key parity with fresh Oracle B;
- `semantic_prepass_used=false`;
- contracted completion;
- no local `/api/v1/tasks` truth.

The four A195B morphology failures must now complete correctly if the source identity still exists.

## Phase 3 — anti-invention / guard controls
Prove the fix did not over-relax grounding. At minimum:
- a two-token invented person not present/derivable from the query must still fail closed;
- a valid person reference combined with an invented/wrong `space` literal must still be rejected or clarified; the morphology fix must not bypass non-reference guards;
- canonical assignee values still require trusted observations where the `assignee` field is used;
- ambiguity remains clarification/fail-closed, never silent guessing.

## Phase 4 — real Browser C
Through the actual UI run:
- `Задачи Александра Жданова в DMS`
- `Задачи Родиона Гаранина в DMS`
- surname-only control for each.

Require the two full-name cases to produce the same source-backed task collections as Oracle B, not generic `V4 ERROR`.
Capture request/response/status/widget/evidence.

## Phase 5 — tiny retained regression
Run once each:
- `Покажи DMS-380 и затем задачи его исполнителя` exact Oracle parity;
- `Покажи открытые задачи в DMS` exact parity;
- WMB-30000 attachment lookup exact live parity;
- clarification continuation once;
- plugin/dummy-55 structural gate.

No full 20-row Task Wave rerun is required.

## Phase 6 — service keepalive
Leave the current-HEAD UI/backend/Task API running after QA. Return frontend/backend/Task API URLs, ports, PIDs, health and exact START_HEAD.

## Allowed output
Create/commit/push **only**:

`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_ASSIGNEE_MORPHOLOGY_FIX_REGATE_195C.md`

## Verdict
Use exactly one:
- `AGENT_CORE_V4_TASK_WAVE_GREEN`
- `AGENT_CORE_V4_TASK_WAVE_REOPENED_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires:
- all four previously failing genitive/dative full-name cases now work against fresh REAL AS21 Oracle B;
- anti-invention controls remain GREEN;
- surname/canonical controls remain GREEN;
- no retained regression;
- Hermes/plugin extensibility intact.

If GREEN, recommendation must be:
**Re-close Wave T (#1-20) and proceed to owner Wave S (#21-32 Sprint/flow) through the existing plugin surface.**

## STOP
After committing/pushing only the QA report and leaving current-HEAD services running, stop and wait for the owner.