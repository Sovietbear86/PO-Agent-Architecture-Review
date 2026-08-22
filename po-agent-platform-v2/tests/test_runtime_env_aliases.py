from po_agent.config.settings import Settings


def test_po_agent_prefixed_as21_settings_are_supported(monkeypatch):
    monkeypatch.delenv("AS21_MODE", raising=False)
    monkeypatch.delenv("TASK_API_BASE_URL", raising=False)
    monkeypatch.setenv("PO_AGENT_AS21_MODE", "task-api")
    monkeypatch.setenv("PO_AGENT_TASK_API_BASE_URL", "http://127.0.0.1:8003")

    settings = Settings(_env_file=None)

    assert settings.as21_mode == "task-api"
    assert settings.task_api_base_url == "http://127.0.0.1:8003"


def test_legacy_as21_settings_keep_working(monkeypatch):
    monkeypatch.delenv("PO_AGENT_AS21_MODE", raising=False)
    monkeypatch.delenv("PO_AGENT_TASK_API_BASE_URL", raising=False)
    monkeypatch.setenv("AS21_MODE", "task-api")
    monkeypatch.setenv("TASK_API_BASE_URL", "http://localhost:8003")

    settings = Settings(_env_file=None)

    assert settings.as21_mode == "task-api"
    assert settings.task_api_base_url == "http://localhost:8003"
