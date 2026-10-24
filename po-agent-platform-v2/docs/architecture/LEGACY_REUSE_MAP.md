# Legacy Reuse Map

This document maps legacy components to their intended v2 destinations.

## Legend

- ✅ **YES** - Can be directly reused
- ⚠️ **PARTIAL** - Requires modification
- ❌ **NO** - Should not be reused (architectural issue)

---

## ✅ SWTR Client

**Path:** `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/swtr_client.py`
**Type:** transport
**Target Module:** `adapters.swtr`

**Responsibility:** SWTR REST API client with personal access token

**Reuse Decision:** YES

**Risks:**
- Bearer token authentication may not work (requires PLATFORM_SESSION cookie)
- May need proxy/ SynGX integration
- Transport-only code should be reused, not authentication

**Notes:** Extract transport logic only. Do not copy authentication.

## ⚠️ MCP Server - s21_mcp_proxy.py

**Path:** `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/s21_mcp_proxy.py`
**Type:** mcp
**Target Module:** `orchestration`

**Responsibility:** stdio-to-http proxy for agent

**Reuse Decision:** PARTIAL

**Risks:**
- Old architecture may have overlapping responsibilities
- Stdio-to-HTTP proxy is needed for new design
- Multiple MCP servers caused conflicts in old design

**Notes:** Reuse transport only. Avoid overlapping server architecture.

## ⚠️ MCP Server - jira_mcp_server.py

**Path:** `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/jira_mcp_server.py`
**Type:** mcp
**Target Module:** `adapters.jira`

**Responsibility:** Jira MCP server

**Reuse Decision:** PARTIAL

**Risks:**
- Old architecture may have overlapping responsibilities
- Stdio-to-HTTP proxy is needed for new design
- Multiple MCP servers caused conflicts in old design

**Notes:** Reuse transport only. Avoid overlapping server architecture.

## ⚠️ MCP Server - mcp-swtr/mcp_server.py

**Path:** `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/mcp-swtr/mcp_server.py`
**Type:** mcp
**Target Module:** `adapters.swtr`

**Responsibility:** SWTR FastMCP server

**Reuse Decision:** PARTIAL

**Risks:**
- Old architecture may have overlapping responsibilities
- Stdio-to-HTTP proxy is needed for new design
- Multiple MCP servers caused conflicts in old design

**Notes:** Reuse transport only. Avoid overlapping server architecture.

## ⚠️ s21-task-agent

**Path:** `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/s21-task-agent`
**Type:** agent
**Target Module:** `orchestration`

**Responsibility:** Task search and analysis agent with skills

**Reuse Decision:** PARTIAL

**Risks:**
- Agent has direct LLM calls for all queries
- Skill routing may need redesign
- Many hardcoded employee names

**Notes:** Reuse skill definitions, not agent implementation.

## ⚠️ Team Performance Agent

**Path:** `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/task-api/src/s21_team_performance`
**Type:** metrics
**Target Module:** `metrics`

**Responsibility:** Team performance analysis with skills

**Reuse Decision:** PARTIAL

**Risks:**
- Metrics calculated by LLM instead of deterministic code
- Duplicated repository access code
- Multiple MCP server calls

**Notes:** Extract deterministic formulas, not LLM logic.

## ✅ Metrics Config - task-api/config/metrics.yaml

**Path:** `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/task-api/config/metrics.yaml`
**Type:** config
**Target Module:** `config`

**Responsibility:** metrics configuration

**Reuse Decision:** YES

**Notes:** Configuration can be reused with minor modifications.

## ✅ Metrics Config - task-api/config/thresholds.yaml

**Path:** `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/task-api/config/thresholds.yaml`
**Type:** config
**Target Module:** `config`

**Responsibility:** thresholds configuration

**Reuse Decision:** YES

**Notes:** Configuration can be reused with minor modifications.

## ✅ Workflow Config - task-api/config/workflow_statuses.yaml

**Path:** `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/task-api/config/workflow_statuses.yaml`
**Type:** config
**Target Module:** `config`

**Responsibility:** workflow status mappings

**Reuse Decision:** YES

**Notes:** Workflow configuration can be directly reused.

## ✅ Workflow Config - task-api/config/status_mapping.yaml

**Path:** `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/task-api/config/status_mapping.yaml`
**Type:** config
**Target Module:** `config`

**Responsibility:** status mapping

**Reuse Decision:** YES

**Notes:** Workflow configuration can be directly reused.

## ⚠️ Team Members Config

**Path:** `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/task-api/config/team_members.yaml`
**Type:** config
**Target Module:** `config`

**Responsibility:** Team member definitions with competencies

**Reuse Decision:** PARTIAL

**Risks:**
- Contains PII data (emails, full names)
- May need to use placeholder/ example data

**Notes:** Use as reference. Do not include PII in public repo.

## ⚠️ API Routes

**Path:** `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/task-api/main.py`
**Type:** api
**Target Module:** `api`

**Responsibility:** FastAPI routes and application entry

**Reuse Decision:** PARTIAL

**Risks:**
- Old API may have overlapping endpoints
- Direct agent calls in routes
- No proper error handling pattern

**Notes:** Reference only. Redesign API for v2.
