# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly:

`qa_assignments/CORE8_SEMANTIC_SLOT_OWNER_FIX_CERTIFICATION_072.md`

## Context

Assignment 071 provided enough evidence for an owner fix:
- A1 import/reference bug is proven and retained;
- A2 recovery-entry bug is proven but reimplemented narrowly from explicit current-query constraints;
- A3 `todo -> open` surface hardcode is unproven and has been removed;
- correction regression is addressed by making current literal constraints authoritative over stale semantic state and by re-grounding `member_login` from `person_raw`/authoritative identities.

## Owner fixes under test

Required ancestors of tested HEAD:
- `167c44615a40d628863739729b5c65dddf91747c`
- `ae2ba4ee7cb4be749a6e113319cd40eddaf546a4`
- `cadb692bcece9f047e86630267345eb3457a25ab`

## Role

QA/tester only.

Do not modify production code, prompts, tests, fixtures, credentials, wrappers, runtime configuration or AS21/SWTR data. Do not repair failures.

## Mandatory rules

1. Fetch/pull `feat/core8-real-query-hardening-v2` and record START_HEAD.
2. Execute Assignment 072 exactly as written.
3. Start fresh/current-checkout runtime and run SWTR health preflight first.
4. Live positive probes use REAL AS21/SWTR only; no fake/mock positive data.
5. Require 100% of explicitly required semantic constraints; do not use ambiguous aggregate metrics.
6. Run genuine correction control 3 times in independent sessions.
7. `todo` must remain a raw user literal at the surface layer; any canonical status mapping must be supported downstream by AS21/domain evidence.
8. `member_login` must never equal arbitrary/full query prose.
9. Commit/push only `qa_reports/CORE8_SEMANTIC_SLOT_OWNER_FIX_CERTIFICATION_072.md`.
10. Do not start Assignment 060/062/073 automatically. STOP.

## Required completion summary

Report at minimum:
- START_HEAD + ancestor proof;
- fresh runtime/SWTR preflight;
- focused automated test counts;
- B1-B7 real probe matrix ×3;
- explicit constraint ledger;
- raw-vs-grounded status evidence;
- correction trace ×3;
- member_login corruption regression verdict;
- HTTP 500 count;
- fake/mock source call count;
- new regressions count;
- READY_FOR_060_FULL_RERUN YES/NO;
- FINAL_VERDICT GREEN/RED;
- report commit SHA.

STOP after Assignment 072.