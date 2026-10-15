# GigaCode — Current Action

## ACTIVE: A229M2.2AR — State preservation RED re-gate

**GigaCode is QA ONLY. No production/config/test code edits. STOP at first RED.**

Previous verdict `AGENT_CORE_V4_GOAL_STATE_PRESERVATION_RED_A229M22A`.
First failure: REAL AS21 DMS-267 `task.lookup` contains a nested raw `task.source_data.swtr_attributes` card; Core `_compact_data` preserved it, yielding ~8343 B > 8192 B continuation cap. M2/M4/C5 carried 0 observations despite source-proven lookup.

### Owner fix (outside Core)
- `api/v1/goal_coverage.py` now applies a strict canonical-field allowlist to compact data, recursively for nested dicts/lists, **before** bytes/cap validation.
- Drops ALL `source_data`, `swtr_attributes`, unbounded descriptions/raw card fields; retains canonical task/key/status/assignee/source, hierarchy, and collection metadata only.
- No raised size cap; retains 8192 B and six-observation cap, REAL_AS21 provenance validation and fail-closed semantics.
- Replaced synthetic oversize test with genuinely oversize canonical `related_keys`; added source-card regression and raw-leak test.
- No Core/planner/registry or UI edits; both goal flags OFF by default. Session authentication remains OPEN deployment blocker.

### P0 — formerly failing boundary FIRST
1. Pull current branch, record TESTED_HEAD and Core hashes vs certified 6fb335d. Worktree clean apart from any preexisting documented unrelated file.
2. Run focused `test_v4_goal_coverage.py` and all previously failing tests. **Zero failures**.
3. Retrieve the **actual REAL AS21 DMS-267 task.lookup observation**, including its nested `source_data.swtr_attributes` card, use production `_build_internal_continuation` to assert:
   - M2/M4/C5 all retain exactly the source-proven lookup;
   - no raw card/source_data/swtr_attributes/description persisted;
   - canonical task key/status/source lineage retained;
   - serialised state <8192 B;
   - no hierarchy absence inferred; actual parent DMS-253 remains a missing goal until `task.hierarchy` executes.
4. Reject artificial-only evidence of success. If real lookup still over cap or empty, RED STOP with exact data/size cause.

### P1 — full regression / OFF controls
- Full V4 blast, Task API SWTR, frontend build; no failure.
- Prove Core 6/6 byte-identical, 54 canonical skills unaffected.
- Both flags OFF = pre-feature public behavior; GOAL guard ON / continuation OFF = A229M2.1R behavior.
- Synthetic truly >8192 B canonical data or >6 candidate observations fail closed, no state, no fabricated facts.
- Nested lists and dictionary raw cards cannot leak after recursive stripping.

### P2 — ON isolated HTTP/dialogue gate
- Only isolated QA stack: `PO_AGENT_V4_GOAL_COVERAGE_GUARD=true` and `PO_AGENT_V4_GOAL_CONTINUATION=true`.
- Actual M1/M2/M4/C5 query cases, compare fresh REAL AS21 oracle for each goal.
- Verify pending clarification carries source-backed proven observations internally; no `data.results`, `continuation_observations`, raw card or unsupported claims in browser JSON.
- Continuation via `clarification_id` restores observations in `HarnessRequest` without client-provided observations.
- No duplicate source reads for proven goals in controlled state-machine replay. Live stochastic planner execution is NOT guaranteed.
- Provider 429, source outage, partial/failure do not masquerade as completed. 15-min TTL, 100-entry bound, expiry sweep, consumed token, restart fails safe.
- Record known session impersonation risk: authenticated ownership is still missing; test but do not assert deployment-ready security.
- No tenant-wide scans, mutations, local fallbacks or forbidden source inference.

### P3 — decision / report
Return EXACTLY:
- `AGENT_CORE_V4_GOAL_STATE_PRESERVATION_GREEN_A229M22AR` only if P0–P2 pass and session-auth deployment blocker remains openly stated.
- `AGENT_CORE_V4_GOAL_STATE_PRESERVATION_RED_A229M22AR` otherwise, first boundary + STOP.

Commit QA report only to:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_GOAL_STATE_PRESERVATION_REGATE_A229M22AR.md`

Provide TESTED_HEAD, REPORT_COMMIT, real lookup pre/post byte sizes, goal evidence/continuation state matrix, counts, Core hashes and OPEN blockers.

No checkpoint, no feature-default flip and no A229M2.2B until owner reviews verdict.
