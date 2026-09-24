# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_212_RELEASE_SEARCH_REGATE

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement release.health.
Do NOT add skills.
Do NOT start the next five-skill batch.
Commit/push only the QA report and QA-only evidence.

## Baseline
A210 Wave S2 is GREEN.
A211 diagnosed the release source defect as bounded Task API code.

Owner fix commit:
`2c630b15e5df019b1e51392429c4042f1f0acaa0`

The fix is intentionally limited to `task-api/app/routers/swtr_read.py`:
- emit live-schema-required `calculatedAttributes=null` for search_versions;
- unwrap the MCP envelope so `versions` is a list;
- preserve pagination metadata;
- no Agent Core/planner/runtime/plugin routing changes.

## Goal
Re-gate `release.search` end-to-end and collect the source evidence required for the subsequent owner implementation of `release.health`.

## Phase 0 — architecture invariant
1. Pull `feat/core8-real-query-hardening-v2`.
2. Record START_HEAD and clean worktree.
3. Diff owner fix against A211 baseline.
4. Prove:
   - only bounded Task API release-source plumbing changed;
   - no Agent Core/planner/runtime changes;
   - release.search remains plugin/registry-discovered;
   - dummy-55 invariant remains GREEN.

Any architecture drift => RED.

## Phase 1 — direct source and Task API parity
Using the same live MCP schema/oracle method as A211:

Probe at least WMB, OLP, STS and DMS.

Require:
- Task API /versions returns 200 whenever direct MCP returns 200;
- exact version/release set parity for source-backed rows;
- DMS zero is treated as authoritative REAL_EMPTY, not source unavailable;
- versions is a JSON list;
- no local/cache fallback;
- pagination metadata remains coherent.

## Phase 2 — adapter parity
Run the production adapter `search_versions_bounded`.

Require exact set parity with Task API/direct MCP for the tested spaces.
No malformed-payload error.
No tenant task scan.
No local factual reads.

## Phase 3 — release.search natural-language gate
Run representative forms:
- `релизы WMB`
- `релизы OLP`
- `релизы DMS`
- `какие релизы есть в WMB`
- one exact/partial real release query from the live source.

Require:
- correct skill load and space resolution;
- exact source parity;
- no product-space-as-release-id confusion;
- multiple results remain a list unless require_single=true;
- DMS source-backed zero is not fabricated into a release.

If the current contract renders a source-backed empty directory as clarification instead of REAL_EMPTY, classify that separately; do not hide it.

## Phase 4 — Browser C
Real UI:
- WMB release list/search;
- OLP release list/search;
- DMS zero-result behavior.

No source-unavailable for healthy source.
No stack/contract/session leakage.

## Phase 5 — release-health linkage oracle
No implementation.

For at least one real WMB/OLP release returned by Phase 1:
1. capture its catalog fields: code/id/name/status/raw;
2. inspect real tasks/raw release attributes in the same space;
3. determine which exact source field and identifier represent release membership;
4. test bounded `task-query?space=<space>&release=<candidate>` with every source-justified identifier candidate (for example code UUID and name), never guessed tenant scans;
5. identify the exact identifier that yields authoritative release membership, or prove the current task-query predicate/field is wrong.

Record:
- release catalog identifier(s);
- task-side attribute code(s);
- matching identifier;
- exact bounded query;
- membership task-key set;
- whether membership completeness is proven.

This evidence will drive the owner implementation of release.health.

## Phase 6 — retained regression
At minimum:
- one Wave S2 metric;
- sprint.health;
- task.lookup;
- person+status task search;
- dummy-55;
- local factual /api/v1/tasks reads = 0;
- no tenant-wide scans.

## Verdict
Use exactly one:
- `RELEASE_SEARCH_GREEN_HEALTH_LINKAGE_READY`
- `RELEASE_SEARCH_GREEN_HEALTH_LINKAGE_BLOCKED`
- `RELEASE_SEARCH_RED`

If GREEN, recommend the smallest owner-side release.health implementation based strictly on Phase 5 evidence.
STOP after report. Do not edit production code.
