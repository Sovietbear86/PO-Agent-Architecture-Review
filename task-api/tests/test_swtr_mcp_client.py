"""Unit coverage for the read-only MCP-SWTR client configuration."""

from app.services.swtr_mcp_client import SWTRMCPClient, SWTRMCPUnavailable


def test_swtr_mcp_client_defaults_to_stdio(monkeypatch):
    """Test that stdio is the default transport (current certified behavior)."""
    for name in (
        "SWTR_MCP_TRANSPORT",
        "SWTR_MCP_SSE_URL",
        "SWTR_MCP_STDIO_ARGS",
        "SWTR_MCP_STDIO_SCRIPT",
    ):
        monkeypatch.delenv(name, raising=False)

    client = SWTRMCPClient()

    # Current production uses stdio as default
    assert client.transport_kind() == "stdio"
    # stdio_command defaults to repository wrapper
    assert "mcp-swtr-wrapper.sh" in client.stdio_command
    # stdio_args is empty when no config provided
    assert client.stdio_args == []


def test_swtr_mcp_client_builds_stdio_config_from_env(monkeypatch):
    monkeypatch.setenv("SWTR_MCP_TRANSPORT", "stdio")
    monkeypatch.setenv("SWTR_MCP_STDIO_COMMAND", "/opt/mcp/.venv/bin/python")
    monkeypatch.setenv("SWTR_MCP_STDIO_ARGS", "/opt/mcp/mcp_server.py --quiet")
    monkeypatch.setenv("SWTR_MCP_STDIO_CWD", "/opt/mcp")
    monkeypatch.setenv("SWTR_TOKEN", "secret-token")
    monkeypatch.setenv("SWTR_MCP_BASE_URL", "https://portal.example/swtr")

    client = SWTRMCPClient()

    assert client.transport_kind() == "stdio"
    assert client.stdio_command == "/opt/mcp/.venv/bin/python"
    assert client.stdio_args == ["/opt/mcp/mcp_server.py", "--quiet"]
    assert client.stdio_cwd == "/opt/mcp"
    assert client._stdio_env() == {
        "BASE_URL": "https://portal.example/swtr",
        "PORT": "0",
        "TOKEN": "secret-token",
    }
    assert "secret-token" not in client._transport_target()


def test_swtr_mcp_client_requires_stdio_command_and_args(monkeypatch):
    """Test that stdio transport fails when default wrapper is missing."""
    monkeypatch.setenv("SWTR_MCP_TRANSPORT", "stdio")
    # Clear all stdio-related env vars to force default lookup
    monkeypatch.delenv("SWTR_MCP_STDIO_COMMAND", raising=False)
    monkeypatch.delenv("SWTR_MCP_STDIO_ARGS", raising=False)
    monkeypatch.delenv("SWTR_MCP_STDIO_SCRIPT", raising=False)
    # Delete the env var that would add the wrapper to stdio_cwd
    monkeypatch.delenv("SWTR_MCP_STDIO_CWD", raising=False)

    client = SWTRMCPClient()

    # Default command should exist (repository wrapper)
    assert client.stdio_command is not None
    assert "mcp-swtr-wrapper.sh" in client.stdio_command
