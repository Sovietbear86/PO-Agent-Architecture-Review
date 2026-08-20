# GigaCode — Current QA Action

## Active assignment

Read and execute exactly:

`qa_assignments/CORE8_SOURCE_BACKED_SPRINT_MEMBERSHIP_RETEST_030.md`

Repository:

`Sovietbear86/PO-Agent-Architecture-Review`

Branch:

`feat/core8-real-query-hardening-v2`

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

After pushing the report, stop. Return:

1. report commit SHA;
2. final verdict;
3. complete report contents.

If execution is blocked, write the blocker and exact required manual action into the same report, commit/push the report, and stop.
