# Assignment 071 — CORE8 Semantic Slot 070 Triage and Clean Re-Certification

## Goal
Resolve the contaminated Assignment 070 result without guessing: separate the owner production fixes from the unauthorized QA production edits in commit `ac17b2035e9c83e77b19d9b1fe1765d8759fb93e`, determine which edits are technically valid, identify the exact remaining 4/36 semantic failures and the genuine-correction failure, and produce evidence for the owner/developer. Do not modify production code.

## Role
QA/tester only. This assignment is diagnostic/certification only.

## Hard rules
1. Fetch/pull `feat/core8-real-query-hardening-v2`; record START_HEAD.
2. Do NOT edit production code, prompts, tests, fixtures, wrappers, runtime config, credentials or AS21/SWTR data.
3. Do NOT revert or amend `ac17b20`; analyze it as evidence. Owner decides what to retain/revert.
4. Live positive tests use REAL AS21/SWTR only. No fake/mock positive data.
5. Run runtime freshness + SWTR health before live probes.
6. If a long real-data matrix is required, it may run autonomously/background, but report exact commands, completion status and results.
7. Commit/push only the QA report for 071. STOP afterward.

## Phase A — Commit forensics
Compare parent of `ac17b20` with `ac17b20` and classify every production-code hunk separately:
- A1 module-level `_SPRINT_ID_FULL` / `_TASK_KEY_FULL` import/reference fix;
- A2 recovery-entry condition change;
- A3 `status_semantic` mapping (`todo`, Russian status words -> `open`);
- any other production hunk.

For each hunk report: BUG_PROVEN / FIX_TECHNICALLY_VALID / FIX_UNPROVEN / FIX_UNSAFE, with code evidence and tests that prove the classification.

Special requirements:
- Verify whether A1 is a genuine NameError/attribute bug in the owner safety-net.
- Verify A2 does not cause unnecessary recovery for queries that legitimately contain only one/two filters, exact task lookup, sprint-only lookup, or already-grounded slots.
- Treat A3 as UNPROVEN unless AS21/runtime/domain evidence proves the semantic equivalence. Do not assume `todo == open`; do not hardcode business semantics from English/Russian labels without evidence.

## Phase B — Reconstruct clean owner baseline
Without changing the working branch, run the relevant automated/unit tests against the owner baseline immediately before `ac17b20` (or an isolated worktree/temporary checkout) and against `ac17b20`. Do not commit temporary checkout artifacts.

Required comparison:
- semantic slot recovery tests;
- semantic core/frame boundary tests;
- exact task/sprint structural-ID controls;
- anti-hallucination controls.

Report which improvements are attributable to A1/A2/A3 rather than to the original owner fixes `88d602f`, `b9f46a1`, `d2cd375`.

## Phase C — Explain 32/36 exactly
Recalculate the Assignment 070 metric from raw responses. List all 36 expected constraints and identify exactly which four were counted failed. Do not use aggregate prose only.

Check specifically whether the reported `status_semantic 0/9` is arithmetically compatible with `32/36`; flag any inconsistent metric/reporting logic.

For DMS/OLP/CRPV/WMB/STS terminology, distinguish literal token preservation from AS21 entity grounding. Do not label a token a product, sprint or space without real AS21 evidence.

## Phase D — Genuine correction boundary
Reproduce the 070 correction case with fresh independent sessions using REAL runtime:
1. initial query with person + space/sprint + status;
2. correction changing only status.

Trace the first boundary where the corrected value is lost or another slot is corrupted. Determine whether the reported `member_login` corruption is real and identify the responsible function/module. Do not fix it.

Run at least 3 repetitions. Required result: exact input/output frame per turn and FIRST_FAILING_BOUNDARY.

## Phase E — Clean certification probes
Run a compact real-data probe set ×3 after preflight:
- person only;
- explicit sprint ID;
- exact task ID;
- status only;
- person + sprint + status;
- one accessible non-DMS space;
- correction case;
- anti-hallucination negative control.

Record HTTP 500 count and fake/mock source call count.

## Decision gate
Set `READY_FOR_OWNER_FIX = YES` only when the report contains enough evidence to tell the owner exactly which `ac17b20` hunks should be retained/reimplemented and what remaining defect(s) require an owner fix.

Do NOT set `READY_FOR_060_FULL_RERUN = YES` unless all required semantic constraints and correction behavior pass on a clean owner-approved production state. Since QA must not approve its own production edits, an `ac17b20`-only GREEN is insufficient.

## Required report
Create only:
`qa_reports/CORE8_SEMANTIC_SLOT_070_TRIAGE_071.md`

Include:
- START_HEAD and tested SHAs;
- clean runtime/SWTR preflight;
- per-hunk A1/A2/A3 verdict;
- baseline-vs-ac17b20 test comparison;
- explicit 36-constraint ledger and exact four failures;
- metric consistency verdict;
- correction trace ×3 and FIRST_FAILING_BOUNDARY;
- compact real probe matrix ×3;
- HTTP 500 count;
- fake/mock count;
- owner-fix recommendation (no implementation);
- READY_FOR_OWNER_FIX YES/NO;
- READY_FOR_060_FULL_RERUN YES/NO;
- final verdict.

STOP. Do not start Assignment 060/062/072 and do not modify production code.