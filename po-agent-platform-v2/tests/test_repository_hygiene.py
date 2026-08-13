from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parent


def test_local_and_generated_artifacts_are_not_committed():
    forbidden_dirs = {
        REPO / ".venv",
        REPO / ".idea",
        REPO / ".gigaide",
        REPO / "mcp-swtr",  # historical broken gitlink; real source is an external integration
    }
    assert not [str(path.relative_to(REPO)) for path in forbidden_dirs if path.exists()]

    forbidden_files = [
        REPO / ".gigacode" / "settings.json",
        REPO / ".gigacode" / "settings.json.orig",
        REPO / "MyTestProject_1.iml",
    ]
    assert not [str(path.relative_to(REPO)) for path in forbidden_files if path.exists()]

    generated_suffixes = {".bak", ".backup", ".broken", ".iml", ".zip", ".tgz"}
    offenders = []
    for path in REPO.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", "node_modules", "dist", "build", ".pytest_cache", "__pycache__"} for part in path.parts):
            continue
        if path.suffix.casefold() in generated_suffixes:
            offenders.append(str(path.relative_to(REPO)))
    assert offenders == []


def test_production_harness_path_does_not_import_legacy_orchestrator():
    production_roots = [
        PROJECT / "src" / "po_agent" / "api",
        PROJECT / "src" / "po_agent" / "harness",
    ]
    offenders = []
    for root in production_roots:
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "po_agent.orchestration" in text or "from ..orchestration" in text:
                offenders.append(str(path.relative_to(PROJECT)))
    assert offenders == []
