# GigaCode — Current QA Action

## Mandatory context reset

Ignore every assignment, report target and HEAD remembered from an earlier GigaCode session. The repository files below are the only authority for this run.

The active assignment is **032**, not 006, 029, 030, 031 or any other historical assignment. Assignments 029 and 026 must be read as benchmark specifications, but their historical reports must not be updated.

## Active assignment

Read and execute exactly:

`qa_assignments/CORE8_FULL_SEMANTIC_BENCHMARK_032.md`

Repository:

`Sovietbear86/PO-Agent-Architecture-Review`

Branch:

`feat/core8-real-query-hardening-v2`

Expected output path:

`qa_reports/CORE8_FULL_SEMANTIC_BENCHMARK_032.md`

## Mandatory Git preflight

Before starting services or tests:

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `git rev-parse HEAD` as `START_HEAD`.
4. Read this file again from `START_HEAD`.
5. Read `qa_assignments/CORE8_FULL_SEMANTIC_BENCHMARK_032.md` completely, followed by the referenced Assignment 029 and Assignment 026 specifications.
6. Verify all three values below. If any value differs, do not run another assignment and do not modify any historical report; create the expected 032 report with `032_FULL_BENCHMARK = BLOCKED` and exact mismatch evidence, then stop.

```text
ACTIVE_ASSIGNMENT = 032
ACTIVE_ASSIGNMENT_FILE = qa_assignments/CORE8_FULL_SEMANTIC_BENCHMARK_032.md
ALLOWED_REPORT_FILE = qa_reports/CORE8_FULL_SEMANTIC_BENCHMARK_032.md
```

The production commit `319ae1e85311f3123c44c2dd0118b843172aef4d` and the valid Assignment 031 report commit `b5ac573` must both be ancestors of `START_HEAD`:

```bash
git merge-base --is-ancestor 319ae1e85311f3123c44c2dd0118b843172aef4d "$START_HEAD"
git merge-base --is-ancestor b5ac573 "$START_HEAD"
```

If either check fails, report BLOCKED in the allowed 032 report and stop.

## Autonomous execution — no step-by-step confirmation

The repository owner has pre-authorized the complete QA workflow defined by this entrypoint and the active assignment. Execute it end to end without asking for confirmation after each step or before each integration call.

No additional conversational confirmation is required for read-only AS21/SWTR calls, the configured semantic LLM, local service restart/health checks, HTTP diagnostics, test runs, `git switch`, `git pull --ff-only`, Git inspection, or commit/push of the explicitly allowed QA report.

Do not pause with questions such as “continue?”, “run the integration?”, “restart the service?” or “commit the report?”. Ask only if continuing requires an unconfigured credential/permission, an unavoidable platform approval, a write outside the report allowlist, a production/source-data/configuration mutation, a destructive out-of-scope action, or a material scope expansion. Consolidate any unavoidable platform approval to the minimum number of prompts possible.

## Fixed role

GigaCode is QA/tester only.

- Do not modify production code, prompts, adapters, tests, fixtures, acceptance runners, configuration, AS21/SWTR data or learning state.
- Do not repair discovered defects.
- Do not weaken or tune the acceptance oracle.
- Use real AS21/SWTR evidence as required by the active assignment.
- Never commit `.env`, credentials or secrets.

## Allowed Git output

Create, commit and push only the report required by the active assignment:

`qa_reports/CORE8_FULL_SEMANTIC_BENCHMARK_032.md`

An existing machine-readable runner result may also be committed only if the active assignment explicitly allows it.

Before commit, stage explicitly and verify the allowlist:

```bash
git add -- qa_reports/CORE8_FULL_SEMANTIC_BENCHMARK_032.md
git diff --cached --name-only
```

The staged file list must contain exactly the allowed 032 report. If any other path appears, including the runner-generated historical 026 JSON, do not commit until it is unstaged. Never modify or stage a historical report or result.

The commit subject must start with:

`qa: CORE8_FULL_SEMANTIC_BENCHMARK_032`

After pushing the report, stop. Return:

1. report commit SHA;
2. final verdict;
3. complete report contents.

If execution is blocked, write the blocker and exact required manual action into the same report, commit/push the report, and stop.
