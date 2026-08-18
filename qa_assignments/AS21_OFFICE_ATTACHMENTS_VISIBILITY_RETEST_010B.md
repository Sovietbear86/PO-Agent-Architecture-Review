# QA Assignment: AS21-OFFICE-ATTACHMENTS-VISIBILITY-RETEST-010B

## Goal
Verify the small production fix made after A3 GREEN: exact task reads must expose proven AS21 attachment metadata to the canonical `Task.attachments` field, so PO Agent skills can actually see Office attachments instead of only having a separate metadata method.

Production code was already changed by the developer. **Do not modify production code.** Test only and publish the report.

## Primary real case
Use real AS21 task `WMB-30000`.

Required checks:
1. MCP-SWTR SSE is connected.
2. `TaskApiAS21Adapter.source_facts` advertises both `tasks` and `attachments`.
3. `await adapter.get_attachment_metadata("WMB-30000")` returns the real attachment set.
4. `await adapter.get_task("WMB-30000")` returns a canonical Task whose `attachments` list contains the same attachment IDs as the metadata call.
5. At least one real `.xlsx` attachment is present and classified as `AttachmentType.EXCEL`.
6. The `.xlsx` name, id, size and created timestamp are preserved.
7. No file content/download is required for this visibility test; metadata-only read remains read-only.
8. Attachment metadata from another task must not leak into `WMB-30000`.

## Office format matrix
Check recognition/visibility for these families:

- Excel: `.xlsx`, `.xls`, `.xlsm`, `.xlsb`, `.csv`, `.ods`
- Word/text-office: `.doc`, `.docx`, `.docm`, `.rtf`, `.odt`
- PDF: `.pdf`
- Outlook: `.msg`
- PowerPoint/presentation: `.ppt`, `.pptx`, `.pptm`, `.odp`

### Real-data rule
First try to discover real examples in accessible AS21 spaces (WMB, DMS, OLP) by reading attachment metadata only. Do not download file bodies merely to find extensions.

For every family found in real AS21, report:
- task key
- attachment id
- file name
- content type (if provided)
- canonical AttachmentType
- PASS/FAIL visibility

If no real example exists for a family, state `REAL_SAMPLE_NOT_FOUND`; then exercise `_attachment_type()` with a deterministic synthetic filename/MIME only to verify classifier behavior. Keep real-vs-synthetic evidence clearly separated.

PowerPoint currently may classify as `OTHER` because the canonical enum does not yet contain a presentation type. This is acceptable for this retest **only if the attachment is still visible and preserved**. Flag it as a product-model gap rather than a retrieval failure. Do not change the enum yourself.

## Exact-task richness invariant
The key regression target is this:

`get_task("WMB-30000").attachments` MUST NOT be empty when `get_attachment_metadata("WMB-30000")` is non-empty.

The two lists must have identical attachment IDs and counts.

## False-green attacks
Verify:
- malformed task key -> no attachment read / empty result
- nonexistent task -> empty/404-safe result, never another task's files
- unknown extension -> attachment remains visible as `OTHER`
- malformed attachment metadata -> fail closed with explicit source error
- no AS21 write/mutation methods are invoked

## Regression
Run attachment-related targeted tests plus relevant adapter/harness regression. Compare to current branch baseline and report `NEW_CODE_REGRESSIONS_VS_BASE`.

## Required report
Publish:

`qa_reports/AS21_OFFICE_ATTACHMENTS_VISIBILITY_RETEST_010B.md`

Machine-readable footer:

```text
ASSIGNMENT_ID = AS21-OFFICE-ATTACHMENTS-VISIBILITY-RETEST-010B
MCP_SWTR_CONNECTED = YES|NO
WMB_30000_METADATA_ATTACHMENT_COUNT = <n>
WMB_30000_TASK_ATTACHMENT_COUNT = <n>
WMB_30000_ATTACHMENT_IDS_MATCH = YES|NO
WMB_30000_XLSX_VISIBLE = YES|NO
WMB_30000_XLSX_CLASSIFIED_EXCEL = YES|NO
EXCEL_FAMILY = PASS|FAIL|REAL_SAMPLE_NOT_FOUND
WORD_FAMILY = PASS|FAIL|REAL_SAMPLE_NOT_FOUND
PDF_FAMILY = PASS|FAIL|REAL_SAMPLE_NOT_FOUND
MSG_FAMILY = PASS|FAIL|REAL_SAMPLE_NOT_FOUND
POWERPOINT_FAMILY = PASS|FAIL|REAL_SAMPLE_NOT_FOUND
UNKNOWN_EXTENSION_VISIBLE_AS_OTHER = YES|NO
AS21_MUTATIONS_DURING_TEST = 0|<n>
NEW_CODE_REGRESSIONS_VS_BASE = <n>
BLOCKER_COUNT = <n>
READY_FOR_CORE8_011 = YES|NO
```

## Gate
`READY_FOR_CORE8_011 = YES` only if the WMB-30000 exact-task visibility invariant is GREEN, the real XLSX is visible/classified correctly, no mutation occurs, and no new regressions are introduced.