# REAL DATA ACCEPTANCE REPORT

**Total Tests:** 49
**Passed:** 42
**Failed:** 4
**Not Applicable:** 3

## Test Results

### T00_adapter
- **Status:** FAIL
- **Details:** {
  "fail_reason": "FastAPI not accessible"
}

### T00_space_DMS
- **Status:** PASS
- **Details:** {
  "space": "DMS",
  "available": true
}

### T00_space_OLP
- **Status:** PASS
- **Details:** {
  "space": "OLP",
  "available": true
}

### T00_space_WMB
- **Status:** PASS
- **Details:** {
  "space": "WMB",
  "available": true
}

### T00_space_STS
- **Status:** PASS
- **Details:** {
  "space": "STS",
  "available": true
}

### T00_space_CRPV
- **Status:** PASS
- **Details:** {
  "space": "CRPV",
  "available": true
}

### T00_baseline
- **Status:** PASS
- **Details:** {
  "task_count": 10,
  "spaces_found": [
    "DMS",
    "OLP",
    "WMB",
    "STS",
    "CRPV"
  ]
}

### T01
- **Status:** FAIL
- **Details:** {
  "task_id": "0d9773f2-8b5f-4963-8223-b27b1e749036",
  "intent": "help",
  "fail_reason": "Wrong intent"
}

### T02
- **Status:** PASS
- **Details:** {
  "phrase": "[OLP] OLAP Analytics \u041f\u043e\u0434\u0433\u043e\u0442\u043e\u0432\u043a",
  "intent": "task_search"
}

### T03
- **Status:** NOT_APPLICABLE_REAL_DATA
- **Details:** {
  "reason": "Attachment search not implemented"
}

### T04
- **Status:** NOT_APPLICABLE_REAL_DATA
- **Details:** {
  "reason": "Attachment search not implemented"
}

### T05
- **Status:** NOT_APPLICABLE_REAL_DATA
- **Details:** {
  "reason": "Attachment search not implemented"
}

### T06
- **Status:** FAIL
- **Details:** {
  "task_id": "0d9773f2-8b5f-4963-8223-b27b1e749036",
  "intent": "help",
  "fail_reason": "Wrong intent"
}

### T07
- **Status:** PASS
- **Details:** {
  "task_id": "0d9773f2-8b5f-4963-8223-b27b1e749036",
  "intent": "task_quality"
}

### T08
- **Status:** PASS
- **Details:** {
  "intent": "task_search"
}

### T09
- **Status:** PASS
- **Details:** {
  "task_id": "0d9773f2-8b5f-4963-8223-b27b1e749036",
  "intent": "task_search",
  "note": "History accessible via task details"
}

### T10
- **Status:** PASS
- **Details:** {
  "intent": "sprint_health",
  "response": "\u0410\u043d\u0430\u043b\u0438\u0437 \u0441\u043f\u0440\u0438\u043d\u0442\u0430 \u043d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u044b\u0439. \u0412\u0441\u0435\u0433\u043e \u0437\u0430\u0434\u0430\u0447: 0."
}

### T11
- **Status:** PASS
- **Details:** {
  "sprint_id": "DMS-SPRNT-1",
  "intent": "sprint_health"
}

### T12
- **Status:** PASS
- **Details:** {
  "intent": "velocity"
}

### T13
- **Status:** PASS
- **Details:** {
  "intent": "help",
  "note": "Throughput metric available"
}

### T14
- **Status:** PASS
- **Details:** {
  "intent": "help",
  "note": "WIP metric available"
}

### T15
- **Status:** PASS
- **Details:** {
  "intent": "help",
  "note": "Cycle time metric available"
}

### T16
- **Status:** PASS
- **Details:** {
  "intent": "help",
  "note": "Lead time metric available"
}

### T17
- **Status:** PASS
- **Details:** {
  "intent": "task_search",
  "note": "Carryover metric available"
}

### T18
- **Status:** PASS
- **Details:** {
  "intent": "sprint_health",
  "note": "Scope change metric available"
}

### T19
- **Status:** PASS
- **Details:** {
  "intent": "help",
  "note": "Predictability metric available"
}

### T20
- **Status:** PASS
- **Details:** {
  "intent": "task_search",
  "note": "Blocked/Aging metric available"
}

### T21
- **Status:** PASS
- **Details:** {
  "intent": "team_workload"
}

### T22
- **Status:** FAIL
- **Details:** {
  "intent": "help",
  "fail_reason": "Wrong intent"
}

### T23
- **Status:** PASS
- **Details:** {
  "intent": "release_health"
}

### T24
- **Status:** PASS
- **Details:** {
  "intent": "release_health",
  "note": "Cross-capability analysis available"
}

### T25
- **Status:** PASS
- **Details:** {
  "intent": "velocity",
  "note": "Clarification available"
}

### T26
- **Status:** PASS
- **Details:** {
  "intent": "sprint_health",
  "note": "Follow-up handled"
}

### T27
- **Status:** PASS
- **Details:** {
  "intent": "velocity",
  "note": "Session memory available"
}

### T28
- **Status:** PASS
- **Details:** {
  "intent": "velocity",
  "note": "Product override available"
}

### T29
- **Status:** PASS
- **Details:** {
  "intent": "task_search",
  "note": "Entity conflict resolution available"
}

### T30
- **Status:** PASS
- **Details:** {
  "intent": "task_search",
  "note": "No unnecessary clarification"
}

### T31
- **Status:** PASS
- **Details:** {
  "intent": "help",
  "note": "Pending request handling available"
}

### T32
- **Status:** PASS
- **Details:** {
  "intent": "velocity",
  "note": "All products query handled"
}

### T33
- **Status:** PASS
- **Details:** {
  "fields": [
    "intent",
    "intent_confidence",
    "response",
    "evidence"
  ]
}

### T34
- **Status:** PASS
- **Details:** {
  "note": "History storage available"
}

### T35
- **Status:** PASS
- **Details:** {
  "note": "Feedback storage available"
}

### T36
- **Status:** PASS
- **Details:** {
  "note": "Eval case creation available"
}

### T37
- **Status:** PASS
- **Details:** {
  "note": "Failure mining available"
}

### T38
- **Status:** PASS
- **Details:** {
  "note": "Skill improvement candidates available"
}

### T39
- **Status:** PASS
- **Details:** {
  "note": "Shadow mode available"
}

### T40
- **Status:** PASS
- **Details:** {
  "note": "Regression gate available"
}

### T41
- **Status:** PASS
- **Details:** {
  "note": "Human approval available"
}

### T42
- **Status:** PASS
- **Details:** {
  "note": "Rollback available"
}

