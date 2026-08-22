# GigaCode — Current QA Action

## Mandatory context reset

Ignore every assignment, report target and HEAD remembered from an earlier GigaCode session. The repository files below are the only authority for this run.

The active assignment is **046**, not 006, 017, 026, 029, 030, 031, 032, 033, 034, 035, 036, 037, 038, 039, 040, 041, 042, 043, 044, 045 or any other historical assignment.

Assignment 045 is accepted as a valid BLOCKED report. It proved runtime identity and the Task API `/api/v1/swtr-read/*` route contract from the current HEAD. It also proved that simple AS21-backed owner task search works, while independent oracle hydration remains blocked only by unavailable MCP-SWTR transport.

## Active assignment

Read and execute exactly:

`qa_assignments/CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046.md`

Repository:

`Sovietbear86/PO-Agent-Architecture-Review`

Branch:

`feat/core8-real-query-hardening-v2`

Expected output path:

`qa_reports/CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046.md`

## Mandatory Git preflight

Before starting services or tests:

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `git rev-parse HEAD` as `START_HEAD`.
4. Read this file again from `START_HEAD`.
5. Read `qa_assignments/CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046.md` completely.
6. Verify all three values below. If any value differs, do not run another assignment and do not modify any historical report; create the expected 046 report with `046_VERDICT = BLOCKED`, exact mismatch evidence, then stop.

```text
ACTIVE_ASSIGNMENT = 046
ACTIVE_ASSIGNMENT_FILE = qa_assignments/CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046.md
ALLOWED_REPORT_FILE = qa_reports/CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046.md
```

7. Verify no prohibited files are staged.

## Autonomous execution — no step-by-step confirmation

The repository owner has pre-authorized this QA batch. Execute it end to end without asking for confirmation after each routine step, before each integration call, before each owner smoke case, before local service restart, before temporary local diagnostics, or before commit/push of the allowed report.

No additional conversational confirmation is required for read-only AS21/SWTR calls, MCP-SWTR read-only calls, Task API SWTR-read diagnostics, the configured semantic LLM, local service restart/health checks, HTTP diagnostics, test runs, `git switch`, `git pull --ff-only`, Git inspection, or commit/push of the explicitly allowed QA report.

Do not pause with questions such as “continue?”, “run the integration?”, “restart the service?”, “run the next case?”, “apply this QA-helper change?” or “commit the report?”.

Ask only if continuing requires an unconfigured credential/permission, an unavoidable platform approval, a write outside the report allowlist, a production/source-data/configuration mutation, a destructive out-of-scope action, or a material scope expansion.

If your IDE/tool asks for confirmation because of local safety settings, choose the non-destructive one-time approval for the exact allowed command. Do not ask the repository owner for confirmation for routine approved QA steps.

## Fixed role

GigaCode is QA/tester only.

- Do not modify production code, prompts, adapters, tests, fixtures, acceptance runners, QA runners, configuration, AS21/SWTR data, historical reports, roadmap files or learning state.
- Do not modify or commit `qa_026_test_runner_v2.py` or any other runner. If a local helper cannot parse a response, record `QA_INFRA_BLOCKED` or exact helper limitation in the report instead of changing the runner.
- Do not repair discovered production defects.
- Do not weaken or tune the acceptance oracle.
- Do not change canonical query wording.
- Do not run full tenant-wide task sync for 046.
- Do not convert failed, missing or not-executed canonical 017 V2 cases into GREEN.
- Do not publish aggregate/footer metrics that contradict per-case evidence.
- Use real AS21/SWTR evidence as required by the active assignment.
- Never commit `.env`, credentials or secrets.

## Allowed Git output

Create, commit and push only the report required by the active assignment:

`qa_reports/CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046.md`

Before commit, stage explicitly and verify the allowlist:

```bash
git add -- qa_reports/CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046.md
git diff --cached --name-only
```

The staged file list must contain exactly the allowed 046 report. If any other path appears, do not commit until it is unstaged. Never modify or stage a historical report or result.

The commit subject must start with:

`qa: CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046`

After pushing the report, stop. Return:

1. report commit SHA;
2. final verdict;
3. complete report contents.

If execution is blocked, write the blocker and exact required manual action into the same report, commit/push the report, and stop.
