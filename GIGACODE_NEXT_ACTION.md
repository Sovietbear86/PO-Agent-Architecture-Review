# GigaCode — Current QA Action

## Mandatory context reset

Ignore every assignment, report target and HEAD remembered from an earlier GigaCode session. The repository files below are the only authority for this run.

The active assignment is **036**, not 006, 017, 026, 029, 030, 031, 032, 033, 034, 035 or any other historical assignment. Assignment 036 audits the 035 evidence and, if needed, reruns the complete canonical 017 V2 matrix with per-ID evidence.

## Active assignment

Read and execute exactly:

`qa_assignments/CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036.md`

Repository:

`Sovietbear86/PO-Agent-Architecture-Review`

Branch:

`feat/core8-real-query-hardening-v2`

Expected output path:

`qa_reports/CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036.md`

## Mandatory Git preflight

Before starting services or tests:

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `git rev-parse HEAD` as `START_HEAD`.
4. Read this file again from `START_HEAD`.
5. Read `qa_assignments/CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036.md` completely.
6. Read the canonical 017 V2 assignment, referenced detailed specs, and the 035 report completely:
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017.md`
   - `qa_assignments/CORE8_CORRECTION_LOOP_ADDENDUM_017A.md`
   - `qa_reports/CORE8_017V2_COMPLETE_MATRIX_EXECUTION_035.md`
7. Verify all three values below. If any value differs, do not run another assignment and do not modify any historical report; create the expected 036 report with `036_VERDICT = BLOCKED`, exact mismatch evidence, then stop.

```text
ACTIVE_ASSIGNMENT = 036
ACTIVE_ASSIGNMENT_FILE = qa_assignments/CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036.md
ALLOWED_REPORT_FILE = qa_reports/CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036.md
```

The production fix, Assignment 032 GREEN report, Assignment 034 report and Assignment 035 report must all be ancestors of `START_HEAD`:

```bash
git merge-base --is-ancestor 319ae1e85311f3123c44c2dd0118b843172aef4d "$START_HEAD"
git merge-base --is-ancestor 940ee44939dcbca14a7583e167b096525f0e509f "$START_HEAD"
git merge-base --is-ancestor beee3fcc684d8eb8cfafb0f295f8a0706a486d3a "$START_HEAD"
git merge-base --is-ancestor 3777097d9f7a733336de95d5c2d67738e3543f41 "$START_HEAD"
```

If any check fails, report BLOCKED in the allowed 036 report and stop.

## Autonomous execution — no step-by-step confirmation

The repository owner has pre-authorized the complete QA workflow defined by this entrypoint and the active assignment. Execute it end to end without asking for confirmation after each step, before each integration call, or before each test category.

No additional conversational confirmation is required for read-only AS21/SWTR calls, the configured semantic LLM, local service restart/health checks, HTTP diagnostics, test runs, `git switch`, `git pull --ff-only`, Git inspection, or commit/push of the explicitly allowed QA report.

Do not pause with questions such as “continue?”, “run the integration?”, “restart the service?”, “run the next category?”, “execute all 122 cases?” or “commit the report?”.

The following are not valid blockers:

- the matrix has 107+ functional tests;
- CL-01..CL-15 take time;
- the run requires multiple batches;
- a previous report already identified that the full matrix is needed;
- the tester would prefer "manual action" because the suite is long.

Ask only if continuing requires an unconfigured credential/permission, an unavoidable platform approval, a write outside the report allowlist, a production/source-data/configuration mutation, a destructive out-of-scope action, or a material scope expansion.

## Fixed role

GigaCode is QA/tester only.

- Do not modify production code, prompts, adapters, tests, fixtures, acceptance runners, configuration, AS21/SWTR data, historical reports, roadmap files or learning state.
- Do not repair discovered defects.
- Do not weaken or tune the acceptance oracle.
- Do not convert failed, missing or not-executed canonical 017 V2 cases into GREEN.
- Do not publish aggregate/footer metrics that contradict the per-ID evidence table.
- Use real AS21/SWTR evidence as required by the active assignment.
- Never commit `.env`, credentials or secrets.

## Allowed Git output

Create, commit and push only the report required by the active assignment:

`qa_reports/CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036.md`

Before commit, stage explicitly and verify the allowlist:

```bash
git add -- qa_reports/CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036.md
git diff --cached --name-only
```

The staged file list must contain exactly the allowed 036 report. If any other path appears, do not commit until it is unstaged. Never modify or stage a historical report or result.

The commit subject must start with:

`qa: CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036`

After pushing the report, stop. Return:

1. report commit SHA;
2. final verdict;
3. complete report contents.

If execution is blocked, write the blocker and exact required manual action into the same report, commit/push the report, and stop.
