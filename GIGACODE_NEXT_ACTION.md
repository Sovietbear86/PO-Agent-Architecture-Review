# GigaCode — Current Action

## ACTIVE: A229M2.2A — verified observation state preservation (strict independent QA)

**GigaCode QA ONLY. No production/test/config edits. STOP on first RED.**

### Baseline and owner delta

- Feasibility: `AGENT_CORE_V4_SAFE_CONTINUATION_FEASIBILITY_GREEN_A229M22F`.
- Certified Core invariant: 6/6 unchanged vs `checkpoint/v4-complex-task-clarification-green-a229f3r@6fb335d`.
- Owner staged changes ONLY in `api/v1/goal_coverage.py`, `api/v1/__init__.py`, `config/settings.py`, `tests/test_v4_goal_coverage.py`.
- New flag `PO_AGENT_V4_GOAL_CONTINUATION=false` (default OFF), used only with existing `PO_AGENT_V4_GOAL_COVERAGE_GUARD=true`.
- Owner guard preserves bounded compact REAL_AS21-proven observations and their resolver dependencies *before* removing unsafe public `data.results`, and allows the existing `_remember_clarification` / `_prepare_query` to carry them.
- This is stage **STATE PRESERVATION**, not guaranteed missing-goal execution. No new planner functionality.
- Do NOT turn either goal flag or `PO_AGENT_V4_SYNTHESIS_ELISION` on by default. Any ON runs are isolated QA sessions only.
- Security caveat: API currently lacks user authentication and accepts client-provided session_id; do NOT expose this feature via remote/multi-tenant/public deployment. Session ownership remains OPEN and blocks deployment.

### P0 — immediate focused gate + full regression

1. Pull tested branch, clean worktree; record TESTED_HEAD and diff.
2. Prove six Core files byte-identical vs stable checkpoint. No planner/registry/task-source diffs.
3. Run `tests/test_v4_goal_coverage.py`, `tests/test_v4_browser_api_contract.py`, `tests/test_v4_synthesis_elision.py`, `tests/test_runtime_env_aliases.py`, complete V4 blast, Task API SWTR suites, frontend build.
4. **Zero failures.** If any fails, capture exact first failing boundary and STOP; do not fix.

### P1 — real observation shape / offline replay

For M1 (K WMB + S DMS), M2 (DMS-267 lookup + hierarchy), M4 (lookup/hierarchy/collection) and C5 (lookup + related):
- Use exact production REAL AS21 observations, not invented fixture shapes.
- Compare `goal_coverage` before/after; prove only **already executed and independently proven** terminal goals (+ source-backed member.resolve/space.resolve supporting rows) are carried.
- Prove source markers real, not LOCAL/fake, source_complete not false, no source_unavailable, no cross-goal evidence binding.
- Verify restored observations are in `V4Observation.planner_view` shape (step, capability_id, arguments, answer, compact data); preserve key source-backed count/IDs to completion frontier.
- Test case where task collection has 173 tasks and only first 20 keys in compact view: do not claim full key-set available for final rendering. Note re-fetch needs.
- Test >8KB data or >6 observations: fail closed, do not supply unsafe continuation.
- Never pass huge descriptions/raw cards to persistent state.

### P2 — API integration (flag ON isolated)

- With both GOAL_COVERAGE_GUARD and GOAL_CONTINUATION ON, check pending clarification stores observations server-side and `clarification_id` is preserved.
- User-visible JSON contains **no** `continuation_observations`, `continuation_required_skills`, unverified answer, or stripped raw `data.results`.
- After replying to clarification, `_prepare_query` passes restored compact observations to `HarnessRequest`; confirm no reinvention or unauthorized writes.
- With GOAL_CONTINUATION OFF, existing stage 1 behavior byte-equivalent at HTTP contract.
- With both OFF, normal V4 baseline unchanged.
- Multi-intent detection remains conservative; simple composed filters NOT split.
- 0 false COMPLETED / 0 unsupported negative hierarchy claims / 0 source_unavailable-as-zero.

### P3 — continuation behavior and security

- Run state-machine replay: prior K WMB proved, missing S DMS; verify no source re-read of K in controlled valid continuation; mark NOT GUARANTEED for stochastic live planner (separate stage 2).
- Verify successful carried DMS-267 lookup does NOT prove absence of parent; hierarchy is missing until governed `task.hierarchy` executes (oracle parent DMS-253).
- Confirm bounded 15-min TTL, consumed clarification state, no client observation injection, restart loses state fail-safe, 100-entry global pending bound, expiry sweep.
- Verify adversarial case with known session_id+clarification_id; since no authenticated owner binding exists, record **SECURITY OPEN / deployment blocker**. Do not label full session isolation green.
- Verify browser UI behaves correctly on incomplete goal, free-text continuation, failures/429 and normal results.

### P4 — facts, latency, and acceptance

- Report number of resumed goal observations, source reads before/after, remaining goals, LLM calls; report if source timestamps/TTL cannot certify freshness.
- Clarify this implementation **supplies state only**; no deterministic guarantee that the planner attempts all missing goals. This remains A229M2.2B.
- List residual risks: external auth/session ownership, lazy cleanup behavior, stale compact results, lexical detector false negatives, no PARTIAL renderer, repeat-read risk.

Return exactly one:
- `AGENT_CORE_V4_GOAL_STATE_PRESERVATION_GREEN_A229M22A` if P0-P3 functional gates all pass and deployment blocker transparently recorded;
- `AGENT_CORE_V4_GOAL_STATE_PRESERVATION_RED_A229M22A` otherwise (first boundary + STOP).

GREEN is **not** security certification, **not** general multi-goal execution and **not** permission to enable the flag.

Commit report ONLY: `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_GOAL_STATE_PRESERVATION_A229M22A.md`.
Return TESTED_HEAD, REPORT_COMMIT, Core hashes, pass counts, continuation evidence retained, and OPEN risks. No checkpoint or default flip.
