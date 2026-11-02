# GigaCode — CURRENT NEXT ACTION

## A230R3.16-P31-D1-R2-FORECAST-GUARDS-QA

**QA ONLY — no edits or commits.** Preserve local dirty state, all running Review/Public processes and AS21. No source writes, tenant-wide scans, Core V4 modifications or uncontrolled query retries.

### Preceding gate
Independent A230R3.15 D1 **GREEN** on `25eb8dc`: forecast 8/8, V4 297, frontend build exit 0; Task API 112 passed / 21 **pre-existing legacy local-store CRUD** failures (not a D1 regression). Core frozen 6/6. DMS-SPRNT-5 source snapshot as of 2026-11-02T05:35Z: 35 tasks / 20 done / 11 in progress / 4 paused, no committed baseline, closure timestamps available, source lacks official holiday calendar. New `sprint.delivery_forecast` **NOT connected** to live AS21 or UI. D1 source model expects explicit working-day calendar, complete membership and trustworthy timestamps; do not fake them.

### Owner-only D1.1 hardening awaiting independent QA
- `ed67cf8`: normalizes completion timestamps into as_of's timezone before membership-window date checks; rejects remaining-scope projections from fewer than 3 elapsed weekdays, to avoid burst of 3 same-day closes implying 100%.
- `005123c`: 3 synthetic tests for one-day burst and UTC↔local midnight transitions. Pure module and tests only, outside 6 frozen Core files. These patches have not yet been independently run.

### Gates
1. Fetch/verify exact local=remote=TESTED_HEAD. Delta since `25eb8dc` only `delivery_forecast.py`, `test_sprint_delivery_forecast.py`, assignment. Check Core V4 6/6 byte-identical to checkpoint `6fb335d`.
2. Run forecast tests (expected **11/11**) including independent adversarial cases (one-day completion, timezone boundaries, sprint end, full complete, duplicated closing timestamp, missing source working calendar, closure authoritativeness, partial membership, source outage); fail closed and no false high-confidence or committed prediction.
3. Run V4 full regression, Task API source-backed tests, frontend build and report exact numbers, compare 21 legacy Task API failures to recorded baseline; no fake GREEN for test suite as a whole.
4. Verify pure module is still NOT wired to live V4/AS21/UI. Evaluate next D2 integration contract: canonical AS21 sprint key + actual sprint dates/statuses, complete scoped task read, **unique task IDs** for closed-event dedup, source-backed resolved/closed_at (not updated_at), mixed timezone normalization, working weekdays/calendar supplied as a declared product configuration, not an invented AS21 fact. If source calendar unverified, output INSUFFICIENT_EVIDENCE. Do not invent live forecast counts.
5. Inspect for any other forward-looking data leaks. Report exact first failure, tested HEAD, source provenance, bounded source note (no new source queries required), frozen Core, and `D1_R2_GREEN / RED / INCOMPLETE`. STOP.

### Short command
Run A230R3.16-P31-D1-R2-FORECAST-GUARDS-QA from Review GIGACODE_NEXT_ACTION.md. QA only: 11 forecast tests, full regress, timezone/one-day guards, Core 6/6; no fixes/commits. Report and STOP.
