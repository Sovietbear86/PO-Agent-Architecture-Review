# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly this assignment:

`qa_assignments/CORE8_REAL_QUERY_CERTIFICATION_060.md`

## Preconditions

Assignment 067 is complete and GREEN.

Carry-forward evidence from 067:
- fresh PO Agent process from current checkout proven;
- current-checkout import provenance PASS;
- stale `/private/tmp` path absent;
- health after restart PASS;
- live clarification replay A1/A2/A3 PASS;
- replay warning appears on A2/A3 and is not consumed as an answer;
- A→B→A isolation PASS;
- HTTP 500 count = 0;
- new regressions = 0;
- READY_TO_RESUME_060_AND_062 = YES.

067 QA commit: `c6f5f601d8ab225fb44569ce4f242a880e005615`.
Production clarification replay fix verified by 067: `64f4e254446262d4e08c5917133a3e3b926561c8`.

## Report allowlist

Commit and push only the Assignment 060 QA report/artifacts explicitly permitted by `qa_assignments/CORE8_REAL_QUERY_CERTIFICATION_060.md`.

Do not commit JSON, helper scripts, runner changes, wrapper changes, `.env`, credentials, logs, screenshots, historical reports, roadmap edits, production changes, prompts, tests, fixtures, local configuration or AS21/SWTR data unless Assignment 060 explicitly requires a particular QA artifact.

## Role

You are QA/tester only.

The owner/developer makes all production and test changes. Do not repair failures, weaken expectations or alter product behavior during this assignment.

## Mandatory execution rules

1. Fetch/pull `feat/core8-real-query-hardening-v2` first and record `START_HEAD`.
2. Execute Assignment 060 exactly as written; do not silently reduce its scope because 067 passed.
3. Before live tests, prove that the PO Agent and Task API processes used by the run are fresh/current-checkout processes. Run the existing SWTR/runtime health preflight and STOP with an environment classification if it fails.
4. Reuse evidence from 067 only where Assignment 060 explicitly permits it; otherwise perform the check again.
5. Include a genuine-correction control in certification evidence. Do not treat `GENUINE_CORRECTION = NOT_TESTED` from the latest 067 report as certified behavior.
6. Distinguish product defects from environment/test-harness defects. Do not modify production code to make a QA test pass.
7. Do not start Assignment 062 or any later assignment.
8. Produce/update only QA report/artifacts permitted by Assignment 060, commit and push them to the current branch, then STOP.

## Required completion summary

Report at minimum:
- `START_HEAD`;
- fresh-process/current-checkout proof;
- SWTR health/preflight verdict;
- Assignment 060 test matrix and pass/fail counts;
- genuine-correction verdict;
- HTTP 500 count;
- new product regressions count;
- final `060_VERDICT`;
- QA report path;
- commit SHA;
- whether Assignment 062 is ready to start.

## Completion

After completing Assignment 060, commit and push only the allowed QA report/artifacts, then STOP. Do not start Assignment 062.