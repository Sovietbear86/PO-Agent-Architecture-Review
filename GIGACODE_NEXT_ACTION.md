# GigaCode — CURRENT NEXT ACTION

## A230R3.16-R2-P31-D1-FORECAST-ESCAPED-NEWLINE-FIX-QA

**Independent QA ONLY.** Do not edit source code/tests/docs/config, do not commit/push/merge, do not stop user's processes, no AS21 writes or unbounded reads. Preserve untracked QA files and local dirty state. Fetch remote and confirm exact LOCAL_HEAD = REMOTE_HEAD = TESTED_HEAD before testing.

### First failing boundary (R1)
A230R3.16 previous QA on `061c554` was `D1_R2_RED`: `delivery_forecast.py` line 76 contained **literal** backslash-n strings inside a comment, accidentally commenting out timezone normalization and `closure_out_of_scope` verification, and the early-window guard was also swallowed. 9/11 forecast tests passed, 2 failed: `test_reject_incomplete_or_incorrect_closure_evidence` and `test_prevent_one_day_closure_burst_from_promising_100_percent`. One unintended false-READY=100% at sprint start was reproduced. Frozen Core V4 6/6 unchanged, V4 297 passed, frontend built, Task API legacy CRUD 21 failed/112 passed unchanged baseline, source-backed SWTR-read 63 passed. This was a genuine owner D1 regression, **not** AS21 failure.

### Owner-only fix
`29ca0ac` edits **only** `po-agent-platform-v2/src/po_agent/sprint/delivery_forecast.py`:
1. Replace 3 literal `\\n` escapes at line ~76 with real Python source line breaks, so `local_closures = ...astimezone(as_of.tzinfo)` and `if any(...)` execute.
2. Restore the `elapsed < 3 and closed_total < scope_total` fail-closed `insufficient_observation_window` guard.
No other calculator semantics, no V4 plugin/live AS21/UI changes and no Core changes. This new fix is **NOT yet independently QA-verified**.

### Gate 0 — integrity
1. Sync branch HEAD and verify exactly one-owner-file delta since `061c554` plus this QA spec, preserve ALL dirty files. Confirm all 6 frozen Core V4 byte-identical to `6fb335d`.
2. Scan file for literal `\\n` source text in timezone guard, confirm source line separation is valid, and run Python `compileall` on calculator. No hidden source/log leakage.

### Gate 1 — focused + adversarial
1. Run 11 unit tests in `po-agent-platform-v2/tests/test_sprint_delivery_forecast.py`; demand **11/11**. Specifically previously failing cases: post-sprint closure timestamp rejected with `closure_out_of_scope`; UTC date normalized to product-local start/end; one-day same-day 3 closures returns `INSUFFICIENT_EVIDENCE`, not READY 100%.
2. Additional boundary tests (independent, without production edits): 0/1/2 closure events, 3 closure events after 1/2 days with remaining scope, elapsed >=3, all done, negative/out-of-range counts, missing membership/timezone/calendar/AS21, end date, future resolved_at, duplicate task events if adapter later supplies such input. Do not claim caller-dedup is implemented when it is not.
3. Verify calculator is still pure and disconnected from live AS21/UI, no source mutation or fictitious historical predictability. Working calendar and membership must be verified before next integration.

### Gate 2 — regression
V4 full (~297 baseline), source-backed SWTR Task API (~63 baseline), frontend build; run broader Task API and classify previously existing 21 legacy CRUD failures as baseline vs new delta. Do not blanket label Task API green if those remain. Confirm 6/6 Core unchanged. No new LIVE AS21 tests necessary for a pure-module change.

### Verdict and STOP
Return exact TESTED_HEAD, pass/fail per suite, independent adversarial and static checks, proof of line-76 runtime behavior, Core hashes, delta, remaining known gaps. `D1_R2_GREEN` only if required tests and guard behaviors pass. For RED cite first failing line/test and stop. Do not edit anything; optionally keep only untracked QA report. STOP.

### Command
Run A230R3.16-R2-P31-D1-FORECAST-ESCAPED-NEWLINE-FIX-QA from current Review GIGACODE_NEXT_ACTION.md. QA only; 11/11 targeted, recovered timezone/closure/early-window guards, full regression, Core V4 6/6. No fixes/commits. Report and STOP.
