"""Tests for MCP Server with real SWTR data."""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from po_agent.mcp.server import POAgentMCP, MCPResponse, MCPError, Evidence


@pytest.fixture
def mcp_server():
    """Create MCP server."""
    return POAgentMCP()


class TestMCPServerBasic:
    """Tests for basic MCP server operations."""

    @pytest.fixture
    def mcp_server(self):
        """Create MCP server."""
        return POAgentMCP()

    def test_po_query_tool(self, mcp_server: POAgentMCP):
        """Test po_query tool."""
        request = {"tool": "po_query", "arguments": {"query": "покажи задачи Калачанова"}}
        result = asyncio.run(mcp_server.handle_request(json.dumps(request)))

        data = json.loads(result)
        assert data["result"]["success"] is True
        assert data["result"]["tool"] == "po_query"
        assert "TODO: Implement full query processing" in data["result"]["warnings"]

    def test_find_tasks_tool(self, mcp_server: POAgentMCP):
        """Test find_tasks tool."""
        request = {"tool": "find_tasks", "arguments": {"search_term": "task", "limit": 10}}
        result = asyncio.run(mcp_server.handle_request(json.dumps(request)))

        data = json.loads(result)
        assert data["result"]["success"] is True
        assert data["result"]["tool"] == "find_tasks"
        assert "tasks" in data["result"]["result"]

    def test_analyze_sprint_tool(self, mcp_server: POAgentMCP):
        """Test analyze_sprint tool."""
        request = {"tool": "analyze_sprint", "arguments": {"sprint_id": "DMS-SPRNT-1"}}
        result = asyncio.run(mcp_server.handle_request(json.dumps(request)))

        data = json.loads(result)
        assert data["result"]["success"] is True
        assert data["result"]["tool"] == "analyze_sprint"
        assert "health_status" in data["result"]["result"]

    def test_analyze_team_tool(self, mcp_server: POAgentMCP):
        """Test analyze_team tool."""
        request = {"tool": "analyze_team", "arguments": {"team_members": ["Kalachanov.V.V"]}}
        result = asyncio.run(mcp_server.handle_request(json.dumps(request)))

        data = json.loads(result)
        assert data["result"]["success"] is True
        assert data["result"]["tool"] == "analyze_team"
        assert "team_members" in data["result"]["result"]

    def test_analyze_release_tool(self, mcp_server: POAgentMCP):
        """Test analyze_release tool."""
        request = {"tool": "analyze_release", "arguments": {"release_id": "DMS-REL-1"}}
        result = asyncio.run(mcp_server.handle_request(json.dumps(request)))

        data = json.loads(result)
        assert data["result"]["success"] is True
        assert data["result"]["tool"] == "analyze_release"
        assert "scope" in data["result"]["result"]


class TestMCPServerSWTR:
    """Tests for MCP Server with real SWTR data."""

    def test_po_query_with_real_team_member(self, mcp_server: POAgentMCP):
        """Test po_query with real team member reference."""
        request = {
            "tool": "po_query",
            "arguments": {
                "query": "покажи задачи Калачанова в спринте DMS-SPRNT-1"
            }
        }
        result = asyncio.run(mcp_server.handle_request(json.dumps(request)))

        data = json.loads(result)
        assert data["result"]["success"] is True
        assert "Калачанова" in data["result"]["result"]["query"]

    def test_find_tasks_with_sprint_filter(self, mcp_server: POAgentMCP):
        """Test find_tasks with sprint filter."""
        request = {
            "tool": "find_tasks",
            "arguments": {
                "sprint_id": "DMS-SPRNT-1",
                "assignee": "Kalachanov.V.V",
            }
        }
        result = asyncio.run(mcp_server.handle_request(json.dumps(request)))

        data = json.loads(result)
        assert data["result"]["success"] is True
        assert "sprint_id" in data["result"]["result"]["query"]

    def test_analyze_sprint_with_real_team(self, mcp_server: POAgentMCP):
        """Test analyze_sprint with real team members."""
        team_members = [
            "Kalachanov.V.V",
            "Garanin.R.V",
            "Agataeva.A.Z",
            "Dolgovskoy.E.N",
        ]

        request = {
            "tool": "analyze_sprint",
            "arguments": {
                "sprint_id": "DMS-SPRNT-1",
                "team_members": team_members,
            }
        }
        result = asyncio.run(mcp_server.handle_request(json.dumps(request)))

        data = json.loads(result)
        assert data["result"]["success"] is True

    def test_analyze_team_with_multiple_members(self, mcp_server: POAgentMCP):
        """Test analyze_team with multiple real team members."""
        team_members = [
            "Kalachanov.V.V",
            "Garanin.R.V",
            "Agataeva.A.Z",
            "Dolgovskoy.E.N",
            "Kryukov.V.A",
        ]

        request = {
            "tool": "analyze_team",
            "arguments": {
                "team_members": team_members,
                "include_metrics": True,
            }
        }
        result = asyncio.run(mcp_server.handle_request(json.dumps(request)))

        data = json.loads(result)
        assert data["result"]["success"] is True
        assert data["result"]["result"]["team_members"] == team_members

    def test_analyze_release_with_sprints(self, mcp_server: POAgentMCP):
        """Test analyze_release with real sprint linkage."""
        request = {
            "tool": "analyze_release",
            "arguments": {
                "release_id": "DMS-REL-1",
                "sprints": ["DMS-SPRNT-1", "DMS-SPRNT-2", "DMS-SPRNT-3"],
            }
        }
        result = asyncio.run(mcp_server.handle_request(json.dumps(request)))

        data = json.loads(result)
        assert data["result"]["success"] is True
        assert "sprint_linkage" in data["result"]["result"]


class TestMCPServerRealTeamIntegration:
    """Integration tests with real SWTR team data."""

    def test_full_workflow_with_real_team(self, mcp_server: POAgentMCP):
        """Test full MCP workflow with real team members."""
        # Step 1: po_query for Kalachanov.V.V
        request1 = {
            "tool": "po_query",
            "arguments": {
                "query": "покажи задачи Калачанова из спринта DMS-SPRNT-1"
            }
        }
        result1 = asyncio.run(mcp_server.handle_request(json.dumps(request1)))
        assert json.loads(result1)["result"]["success"] is True

        # Step 2: find_tasks for Garanin.R.V
        request2 = {
            "tool": "find_tasks",
            "arguments": {
                "search_term": "баг",
                "assignee": "Garanin.R.V",
            }
        }
        result2 = asyncio.run(mcp_server.handle_request(json.dumps(request2)))
        assert json.loads(result2)["result"]["success"] is True

        # Step 3: analyze_sprint for Agataeva.A.Z
        request3 = {
            "tool": "analyze_sprint",
            "arguments": {
                "sprint_id": "OLP-SPRNT-5",
                "team_members": ["Agataeva.A.Z"],
            }
        }
        result3 = asyncio.run(mcp_server.handle_request(json.dumps(request3)))
        assert json.loads(result3)["result"]["success"] is True

        # Step 4: analyze_team for Dolgovskoy.E.N
        request4 = {
            "tool": "analyze_team",
            "arguments": {
                "team_members": ["Dolgovskoy.E.N", "Kryukov.V.A"],
            }
        }
        result4 = asyncio.run(mcp_server.handle_request(json.dumps(request4)))
        assert json.loads(result4)["result"]["success"] is True

        # Step 5: analyze_release for Kryukov.V.A
        request5 = {
            "tool": "analyze_release",
            "arguments": {
                "release_id": "WMB-REL-2024",
                "sprints": ["WMB-SPRNT-1", "WMB-SPRNT-2"],
            }
        }
        result5 = asyncio.run(mcp_server.handle_request(json.dumps(request5)))
        assert json.loads(result5)["result"]["success"] is True

    def test_all_team_members_query(self, mcp_server: POAgentMCP):
        """Test MCP tools with all team members from team_members.yaml."""
        team_members = [
            "Kalachanov.V.V",
            "Garanin.R.V",
            "Agataeva.A.Z",
            "Dolgovskoy.E.N",
            "Kryukov.V.A",
            "Shaldunov.A.V",
            "Saldunov.A.V",
            "Olga-3081",
            "olp_3081",
            "dolgovskoy_dms",
            "dolgovskoy_olp",
        ]

        for member in team_members:
            request = {
                "tool": "find_tasks",
                "arguments": {
                    "assignee": member,
                    "limit": 5,
                }
            }
            result = asyncio.run(mcp_server.handle_request(json.dumps(request)))
            assert json.loads(result)["result"]["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
