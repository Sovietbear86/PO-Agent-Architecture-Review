# Final Hardening Status — PO Agent Platform v2

## Scope

This document is the release/merge-readiness checkpoint for the recovered Harness implementation on `chatgpt-harness-recovery`.

## Product gates

| Gate | Status | Notes |
|---|---|---|
| Canonical Skill catalog | PASS | 54 Skills implemented; source readiness is evaluated separately. |
| Deterministic metrics | PASS | Sprint/team/release/PO metrics are code-calculated, not LLM-calculated. |
| AS21 boundary | PASS | `TaskApiAS21Adapter` is async and fail-closed. |
| Source readiness | PASS | Missing history/attachments/snapshots/competencies/timeline are explicit. |
| Task-api E2E contract | PASS | Mocked HTTP -> adapter -> Harness -> API response acceptance coverage. |
| Failure semantics | PASS | Source outage, unsupported capability and malformed protocol are typed failures. |
| Operational history | PASS | Append-only execution trace with versions/evidence/warnings. |
| Session context | PASS | Scoped separately from operational history. |
| Feedback/eval loop | PASS | Explicit feedback can seed versioned eval cases. |
| Failure mining | PASS | Deterministic clustering of repeated eval failures. |
| Improvement candidate | PASS | Candidates are inert drafts (`apply=false`). |
| Shadow/offline evaluation | PASS | Baseline and candidate evaluated on the same corpus. |
| Regression gate | PASS | Default policy permits zero regressions and requires measurable improvement. |
| Human approval | PASS | Promotion requires explicit approval. |
| Version promotion/rollback | PASS | Auditable and reversible. |
| Recovery frontend build | PASS | TypeScript + Vite production build is a blocking CI gate. |
| Hermetic backend regression | PASS | Blocking CI gate without real external services. |
| Legacy full suite | DIAGNOSTIC | Non-blocking by design; contains real-service and retired-contract debt. |

## Runtime modes

### `fake`

Use for deterministic development, acceptance tests and UI work. It advertises tasks, sprints, releases, history and attachment fixtures.

### `task-api`

Production-facing boundary. It advertises only source facts actually proven by the current task-api contract: tasks, sprints and releases. Declared team profiles are injected from canonical `team_members.yaml` when available.

Do not treat unavailable source facts as empty data.

## Source-gated Skills

The code implementation exists for all canonical Skills, but runtime availability depends on facts:

- task history / time-in-status / cycle-time / lead-time require `history`;
- attachment search requires `attachments`;
- sprint carryover and scope change require `sprint_snapshots`;
- competency match and assignee recommendation require `team_competencies`;
- release forecast requires `release_timeline`.

This distinction is intentional: `implemented != source-ready`.

## External prerequisites before real AS21 acceptance

1. Start a task-api instance that can reach the target SWTR/AS21 environment.
2. Set `AS21_MODE=task-api` and `TASK_API_BASE_URL`.
3. Provide `TEAM_CONFIG_PATH` or place canonical `team_members.yaml` at an auto-probed location.
4. Run `GET /api/v1/health` and confirm `source_status=healthy`.
5. Execute the real-data checklist against permitted team spaces/products.
6. Do not enable history/attachment/snapshot/timeline readiness until those source contracts are backed by actual APIs or persisted facts.

## Merge readiness

`clean-public-release` has now been merged into the recovery branch. The public-cleanup delta for the security-sensitive recovery artifacts is preserved: old `.config` auth/session files are absent, canonical team config matches the public baseline, and `.config/` is ignored at repository level.

Draft PR #1 is conflict-free (`mergeable=true`). The final merge should happen only after the latest blocking CI lanes are green.

## Definition of done for this recovery

- [x] 54 canonical Skills implemented
- [x] source readiness / capability gating
- [x] fake-to-task-api runtime switch
- [x] grounded competency matching
- [x] sprint snapshot contracts and metrics
- [x] release timeline contract and bounded forecast
- [x] typed source failure semantics
- [x] mocked task-api E2E path
- [x] AI-PDLC feedback/eval/improvement loop
- [x] human approval, promotion and rollback
- [x] rebuilt PO Workspace UI
- [x] blocking recovery CI suite
- [x] hermetic regression suite
- [x] frontend build gate
- [x] public-cleanup baseline synchronized
- [x] draft PR opened and conflict-free
- [ ] real corporate AS21/SWTR acceptance test from an environment with network/auth access

The last unchecked item is an environment acceptance activity, not an architectural implementation gap.
