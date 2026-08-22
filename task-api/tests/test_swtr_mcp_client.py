"""Unit coverage for the read-only MCP-SWTR client configuration."""

from app.services.swtr_mcp_client import SWTRMCPClient, SWTRMCPUnavailable


def test_swtr_mcp_client_defaults_to_sse(monkeypatch):
    for name in (
        "SWTR_MCP_TRANSPORT",
        "SWTR_MCP_SSE_URL",
        "SWTR_MCP_STDIO_ARGS",
        "SWTR_MCP_STDIO_SCRIPT",
    ):
        monkeypatch.delenv(name, raising=False)

    client = SWTRMCPClient()

    assert client.transport_kind() == "sse"
    assert client.sse_url == "http://127.0.0.1:3000/sse"


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
    monkeypatch.setenv("SWTR_MCP_TRANSPORT", "stdio")
    monkeypatch.setenv("SWTR_MCP_STDIO_COMMAND", "")
    monkeypatch.delenv("SWTR_MCP_STDIO_ARGS", raising=False)
    monkeypatch.delenv("SWTR_MCP_STDIO_SCRIPT", raising=False)

    client = SWTRMCPClient()

    try:
        client._build_transport()
    except SWTRMCPUnavailable as exc:
        assert "SWTR_MCP_STDIO_COMMAND" in str(exc)
    else:
        raise AssertionError("stdio transport without command and args must fail closed")
