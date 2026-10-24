import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "diagnostic_runner.py"
spec = importlib.util.spec_from_file_location("diagnostic_runner", MODULE_PATH)
assert spec and spec.loader
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_redact_removes_bearer_jwt_and_named_secrets():
    text = (
        "Authorization: Bearer eyJabc.def.ghi\n"
        "TOKEN=super-secret-value\n"
        "platform_session: cookie-value\n"
    )
    redacted = runner.redact(text)
    assert "super-secret-value" not in redacted
    assert "cookie-value" not in redacted
    assert "eyJabc.def.ghi" not in redacted
    assert "<REDACTED>" in redacted or "<REDACTED_JWT>" in redacted


def test_classification_preserves_competing_non_code_root_causes():
    categories = runner.classify("Traceback: request failed with 403 Forbidden", 1)
    assert "AUTH" in categories
    assert "CODE" in categories


def test_success_has_no_failure_classification():
    assert runner.classify("all good", 0) == []
