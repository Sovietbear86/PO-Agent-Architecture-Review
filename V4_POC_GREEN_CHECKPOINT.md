# PO Agent V4 — Representative POC GREEN Rollback Checkpoint

**Status:** AUTHORITATIVE PLAN ADDENDUM / ROLLBACK LOCK  
**Locked:** 2026-09-15  
**Reason:** preserve the last independently certified working V4 state before the V4-PLUGIN architecture migration.

## 1. Frozen working state

Assignment 188 independently certified the representative V4 backend POC as:

`AGENT_CORE_V4_REPRESENTATIVE_POC_GREEN`

The exact immutable commit is:

`0f03fca14fe078c86dca961362915e10cc985401`

A permanent rollback/reference branch has been created at that exact commit:

`checkpoint/v4-poc-green-a188`

Certification report:

`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_COMPLETION_CONTRACT_REGATE_188.md`

This checkpoint is the authoritative **pre-plugin-migration known-good V4 baseline**.

## 2. What this checkpoint proves

At this checkpoint the existing V4 runtime has independently proven, against fresh REAL AS21:

- representative skill-native V4 operation is GREEN;
- DMS-380 lookup → assignee → tasks: 10/10 exact Oracle parity;
- second lookup → assignee → tasks family: 5/5 exact Oracle parity;
- mixed matrix and unseen combinations are GREEN;
- current-sprint collections and retained B1/B2 fixes are GREEN;
- A183 period/list/non-roster scenarios are GREEN;
- safety and fail-closed negative controls are GREEN;
- deterministic post-observation completion is proven: successful contracted trajectories finish through `runtime_contract`, not stochastic planner `READY`;
- `semantic_prepass_used=false` remains true;
- no entity/query hardcode is required for the certified completion mechanism;
- REAL AS21 remains authoritative.

Known pre-existing issue remains explicitly outside this GREEN proof: the unscoped Cyrillic query `Задачи Семавина` may be corrupted by Qwen planner tokenization. It is a catalog/reliability regression item to close before full 54/54 release certification; it must not be fixed by person-specific hardcode.

## 3. Non-regression rule for all work after A188

**Nothing after this checkpoint may silently trade already-proven behavior for architectural cleanliness or new breadth.**

For V4-PLUGIN, V4-BROWSER, 54-skill migration and later V4 work:

1. The A188 GREEN scenarios are mandatory regression truth.
2. Existing working planner → skill → capability → REAL AS21 → runtime-completion behavior must be preserved unless a replacement is independently proven equivalent or better.
3. A new architecture change that breaks an A188-certified scenario is RED, even if its new feature works.
4. Do not delete or rewrite the current working path merely because a cleaner abstraction exists.
5. Prefer strangler/extraction/refactoring around the proven runtime: move registration/discovery outward while preserving observable behavior.
6. Existing production handlers/capabilities may be wrapped or registered; their business semantics must not be casually reimplemented.
7. Every architecture milestone must compare against this checkpoint before being called GREEN.

## 4. Rollback rule

If V4-PLUGIN or a subsequent architectural migration causes a regression that cannot be bounded and repaired without destabilizing the certified runtime:

- STOP the migration;
- preserve the failed branch/commit for diagnosis;
- compare against `checkpoint/v4-poc-green-a188`;
- use commit `0f03fca14fe078c86dca961362915e10cc985401` as the exact known-good recovery point;
- do not continue stacking fixes on top of an unbounded regression;
- resume migration only after the first failing boundary is understood and the A188 regression gate is restored.

Rollback is a safety mechanism, not a decision to abandon V4. The architectural direction remains V4 unless an explicit architecture decision changes it.

## 5. V4 transition order after this checkpoint

The authoritative execution order is:

```text
A188 REPRESENTATIVE POC GREEN (this checkpoint)
        ↓
V4-PLUGIN
pluginized Skill/Capability Registry + discovery
        ↓
V4-BROWSER / UI + widgets
        ↓
progressive migration to all 54 production skills
        ↓
full 54-skill A/B/C + browser E2E + regression certification
        ↓
V4 RELEASE gate
```

GVS5H / multi-agent analytical orchestration remains **DEFERRED_TO_V5** and must not be introduced during the V4 migration.

## 6. V4-PLUGIN success condition

The next architecture milestone is an **extraction/pluginization**, not a behavioral rewrite.

The V4-PLUGIN gate is GREEN only when:

- skills can be discovered/registered without changing Agent Core orchestration;
- capabilities/handlers are registered through stable contracts rather than central hardcoded maps;
- completion contracts belong to skill/plugin definitions rather than entity/query-specific runtime branches;
- UI metadata can be attached through a stable plugin contract;
- a new test/dummy 55th skill can be installed/discovered/executed without editing Agent Core;
- all A188 representative scenarios remain GREEN after migration;
- REAL AS21 authority, fail-closed behavior, action-only recovery and deterministic runtime completion remain unchanged;
- no semantic prepass, surname/phrase router, entity hardcode or direct client/tool bypass is introduced.

If these conditions cannot be achieved while preserving A188 behavior, the milestone is RED and the checkpoint above is the rollback/reference state.

## 7. Full V4 objective remains unchanged

V4 is not complete at this checkpoint. Final priority remains:

**fully working PO Agent V4 + all 54 production user-facing skills + real UI with all required working widgets + full end-to-end certification, without regressing behavior already proven GREEN.**
