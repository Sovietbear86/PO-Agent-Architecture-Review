# GigaCode — CURRENT NEXT ACTION

## A230R3.25-R2-P31-D2-R9-WEEKDAY-POLICY-GUARD-QA

**Independent QA ONLY.** No source/test/doc/config/Core code edits, no commits, pushes or merges. Preserve all dirty/untracked local QA artifacts, users' services and source credentials. Fetch origin, verify LOCAL_HEAD=REMOTE_HEAD=TESTED_HEAD. No AS21 writes or tenant-wide scans.

### Previous QA and first failing boundary
GigaCode A230R3.25 QA RED on TESTED_HEAD `1e48ef2`: `task-api/app/services/sprint_forecast_policy.py:37` computed `len(set(weekdays))` before validating tuple entries at line 39. With `working_weekdays=([1], 1)` or `({}, 1)` an uncontrolled TypeError escaped instead of typed ValueError; would be HTTP 500 if enabled. Policy 11/11 original unit tests, 32/34 previous adversarial, forecast existing suites 60/60, calculator 11/11, V4 299, Task API 175 pass/25 known baseline failures, frontend exit 0, frozen Core 6/6. No production policy approved or enabled; AS21 does not provide authoritative terminal status categories.

### Owner fix (NOT independently QA-certified)
- `def3120`: one small owner fix in `task-api/app/services/sprint_forecast_policy.py`: type/range guard executes **before** `set(weekdays)`, preserve explicit tuple requirement, reject unhashable/malformed with `ValueError("forecast_working_calendar_invalid")`; duplicate valid weekday returns `forecast_working_calendar_missing` per existing contract.
- `26a750e`: adds seven negative test cases for malformed tuple entries and non-tuple weekdays.
- No other production changes, no default terminal statuses, no live endpoint/plugin/UI and no Core modifications. **Do not claim live forecast deployed.**

### Gates
1. Exact commit delta since `1e48ef2`: policy module + its test + this spec only; no unauthorized additions. Confirm frozen Core V4 six canonical files byte-identical to `6fb335d`, preserve QA files.
2. Run policy unit test file; expect **18 pytest cases** (prior 11 + new 7), count actual collection and report. Reproduce both original RED cases `([1], 1)` and `({}, 1)`; expect controlled ValueError, not TypeError. Additional adversarial: `working_weekdays=([],1)`, nested dict, bool, float, negative, >=7, valid duplicate, missing, non-tuple, malicious unusual objects, terminal_status_types malformed including unhashable list -> typed fail-closed (not AttributeError/TypeError).
3. Confirm caller-provided explicit authority, approved_at tz-aware, product timezone and weekdays, exact source-declared terminal types; no automatic approval, no synthetic values in production. `Europe/Moscow` and `done` in tests are illustrations only.
4. Run 11 calculator tests, source-proof/collector/projection/validator focused suites, full V4 (~299), Task API source-backed/full regression (25 pre-existing failures), frontend build. Report precise baseline. Core 6/6.
5. Verdict `D2_R9_R2_GREEN` only if all required type guards, regress and source-policy checks pass; else RED first failing line and STOP. Distinguish policy VALIDATED from real business authorization (still not granted) and from live wiring (still absent).
6. QA ONLY. No code fixes/commits. Report exact TESTED_HEAD + test counts and STOP.

### Short command
Run A230R3.25-R2-P31-D2-R9-WEEKDAY-POLICY-GUARD-QA from Review GIGACODE_NEXT_ACTION.md. Independently re-test the unhashable weekday policy fix, 18 unit cases, 34+ adversarial, full regress and frozen Core 6/6. No fixes/commits; report and STOP.
