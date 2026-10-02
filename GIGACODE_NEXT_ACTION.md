# GigaCode — Current Action

## NO ACTIVE ASSIGNMENT — V4 stabilized

The current application state is frozen at:

`checkpoint/v4-stable-product-a229f1r2@9d71a7957035dd71ca0c48a02b1f73b4b5312c4f`

Latest certified functional gate:
`AGENT_CORE_V4_CREATED_PERIOD_GREEN_A229F1R2`

GigaCode remains QA/adversarial tester only. Do not modify production code.

## Next assignment when owner explicitly resumes work

Preferred order:

1. **A229R1 verification only** — re-gate already implemented low-risk latency changes; no new optimization code.
2. **A230 security/read-only + rollback rehearsal**.
3. **A231 final V4 DoD / release-candidate audit**.

Only after a release-candidate checkpoint should new functional evolution resume.

First post-RC candidate improvement:
- generic complex task search using typed plugin constraints (creator/author, status, phrase/text-field, period, space/sprint, etc.);
- the current example `Покажи открытые задачи созданные Гальцовым со словом "дефект" в описании` is a regression scenario, not a phrase-specific route.

Hard rule:
- no Agent Core/planner/runtime/session changes unless owner first proves a release-blocking defect that cannot be solved through plugin/UI/task-api/metadata seams.

Wait for explicit owner instruction before running another assignment.
