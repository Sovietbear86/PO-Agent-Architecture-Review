"""Source-bound SberProject catalogue contract tests (offline, no corporate access)."""
import pytest
from fastapi import HTTPException

from app.routers.sberproject_read import _catalog_response, _source_config


def test_missing_auth_fails_closed(monkeypatch):
    monkeypatch.delenv("SBERPROJECT_CATALOG_READ_URL", raising=False)
    monkeypatch.delenv("SBERPROJECT_READ_ACCESS_TOKEN", raising=False)
    with pytest.raises(HTTPException) as error:
        _source_config()
    assert error.value.status_code == 503
    assert error.value.detail["reason"] == "sberproject_auth_required"


@pytest.mark.parametrize("url", [
    "http://internal.example/releases", "https://user:secret@internal.example/releases",
    "file:///private/tmp/file", "https://internal.example/releases#fragment",
])
def test_untrusted_url_configuration_fails_closed(monkeypatch, url):
    monkeypatch.setenv("SBERPROJECT_CATALOG_READ_URL", url)
    monkeypatch.setenv("SBERPROJECT_READ_ACCESS_TOKEN", "test-token-not-real")
    with pytest.raises(HTTPException):
        _source_config()


def test_pagination_and_lifecycle_preserved_without_fake_task_count():
    payload = {"results": [{"id": "OLP.78", "versionNumber": "1.9.0",
                            "workflowStatus": "RELEASED", "releaseDate": "2026-10-14",
                            "issueKey": "SECRET_SHOULD_NOT_LEAK", "percentDone": 99}],
               "meta": {"has_more": True, "total": 69, "next_offset": 20}}
    result = _catalog_response(payload, "OLP", 20)
    assert result["status"] == "PARTIAL"
    assert result["has_more"] is True
    assert result["next_offset"] == 20
    assert result["versions"][0]["id"] == "OLP.78"
    assert "issueKey" not in result["versions"][0]
    assert "percentDone" not in result["versions"][0]
    assert "task_count" not in result
    assert result["membership_status"] == "SOURCE_UNVERIFIED"


@pytest.mark.parametrize("payload", [
    [], {}, {"results": [], "meta": {}},
    {"results": [{"id": "OLP.78"}], "meta": {"has_more": False}},
    {"results": [{"id": "OLP.78", "versionNumber": "1.9.0"}] * 21, "meta": {"has_more": False}},
])
def test_incomplete_source_is_never_treated_as_empty(payload):
    with pytest.raises(HTTPException):
        _catalog_response(payload, "OLP", 20)
