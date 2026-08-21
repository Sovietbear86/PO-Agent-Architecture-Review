# GigaCode — Current QA Action

## Mandatory context reset

Ignore every assignment, report target and HEAD remembered from an earlier GigaCode session. The repository files below are the only authority for this run.

The active assignment is **030**, not 006, 029 or any other historical assignment. Do not open, rerun or update a historical QA report.

## Active assignment

Read and execute exactly:

`qa_assignments/CORE8_SOURCE_BACKED_SPRINT_MEMBERSHIP_RETEST_030.md`

Repository:

`Sovietbear86/PO-Agent-Architecture-Review`

Branch:

`feat/core8-real-query-hardening-v2`

Expected output path:

`qa_reports/CORE8_SOURCE_BACKED_SPRINT_MEMBERSHIP_RETEST_030.md`

## Mandatory Git preflight

Before starting services or tests:

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `git rev-parse HEAD` as `START_HEAD`.
4. Read this file again from `START_HEAD`.
5. Read `qa_assignments/CORE8_SOURCE_BACKED_SPRINT_MEMBERSHIP_RETEST_030.md` completely.
6. Verify all three values below. If any value differs, do not run another assignment and do not modify any historical report; create the expected 030 report with `030_NARROW_GATE = BLOCKED` and exact mismatch evidence, then stop.

```text
ACTIVE_ASSIGNMENT = 030
ACTIVE_ASSIGNMENT_FILE = qa_assignments/CORE8_SOURCE_BACKED_SPRINT_MEMBERSHIP_RETEST_030.md
ALLOWED_REPORT_FILE = qa_reports/CORE8_SOURCE_BACKED_SPRINT_MEMBERSHIP_RETEST_030.md
```

The production commit `fe1b5990e9234fdf959eaccec9187755c4161629` must be an ancestor of `START_HEAD`:

```bash
git merge-base --is-ancestor fe1b5990e9234fdf959eaccec9187755c4161629 "$START_HEAD"
```

If this check fails, report BLOCKED in the allowed 030 report and stop.

## Fixed role

GigaCode is QA/tester only.

- Do not modify production code, prompts, adapters, tests, fixtures, acceptance runners, configuration, AS21/SWTR data or learning state.
- Do not repair discovered defects.
- Do not weaken or tune the acceptance oracle.
- Use real AS21/SWTR evidence as required by the active assignment.
- Never commit `.env`, credentials or secrets.

## Allowed Git output

Create, commit and push only the report required by the active assignment:

`qa_reports/CORE8_SOURCE_BACKED_SPRINT_MEMBERSHIP_RETEST_030.md`

An existing machine-readable runner result may also be committed only if the active assignment explicitly allows it.

Before commit, stage explicitly and verify the allowlist:

```bash
git add -- qa_reports/CORE8_SOURCE_BACKED_SPRINT_MEMBERSHIP_RETEST_030.md
git diff --cached --name-only
```

The staged file list must contain only the allowed 030 report, plus an existing machine-readable result explicitly permitted by Assignment 030. If any other path appears, do not commit until it is unstaged. In particular, never modify or stage `qa_reports/AS21_A3_ATTACHMENT_WIRING_RETEST_006.md`.

The commit subject must start with:

`qa: CORE8_SOURCE_BACKED_SPRINT_MEMBERSHIP_RETEST_030`

After pushing the report, stop. Return:

1. report commit SHA;
2. final verdict;
3. complete report contents.

If execution is blocked, write the blocker and exact required manual action into the same report, commit/push the report, and stop.
