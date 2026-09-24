# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_211_RELEASE_DIAGNOSTIC

GigaCode role: QA/adversarial tester only. No production changes.

Baseline: A210 GREEN.
Checkpoint: checkpoint/v4-wave-s2-green-a210

## Goal
Diagnose release search and release health without changing code.

1. Inspect live search_versions schema.
2. Run direct source calls for DMS and record exact request/response or exact error.
3. Compare direct source with /api/v1/swtr-read/versions.
4. Compare Task API output with the production adapter used by release.search.
5. If source works, test natural-language release search in the agent and Browser C.
6. Inventory release.health: existing skill/capabilities, live release membership path, task-by-release path, available health signals.
7. Run minimal retained regression: one Wave S2 metric, sprint.health, task lookup, person+status search, dummy-55, zero local factual reads.

Report the first failing boundary and the smallest owner fix.

Verdict exactly one:
- RELEASE_SOURCE_READY_FOR_OWNER_FIX
- RELEASE_SOURCE_EXTERNAL_BLOCKED
- RELEASE_SOURCE_ALREADY_HEALTHY

Stop after the report. Do not implement fixes or start another batch.
