import subprocess
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parent


def test_local_and_generated_artifacts_are_not_committed():
    """Test that generated/ignored files are NOT committed to Git.

    Key distinction: This test checks Git tracking status, not file existence.
    Local-only config files like .gigacode/settings.json may exist but must be:
    1. In .gitignore OR
    2. Untracked (git ls-files returns empty)
    """
    # Check IDE dirs are NOT tracked by Git (they may exist locally)
    forbidden_dirs = {
        ".venv",
        ".idea",
        ".gigaide",
        "mcp-swtr",  # historical broken gitlink; real source is an external integration
    }
    tracked = []
    for dir_name in forbidden_dirs:
        result = subprocess.run(
            ["git", "ls-files", dir_name],
            capture_output=True,
            text=True,
            cwd=REPO
        )
        if result.stdout.strip():
            tracked.append(dir_name)
    assert tracked == [], f"Tracked forbidden directories: {tracked}"

    # For .gigacode/settings.json and settings.json.orig:
    # - They MUST exist in working directory (local GigaCode config)
    # - They MUST NOT be tracked by Git
    # - They MUST be in .gitignore
    gigacode_settings = REPO / ".gigacode" / "settings.json"
    gigacode_settings_orig = REPO / ".gigacode" / "settings.json.orig"
    
    # Check files exist (required for local GigaCode operation)
    assert gigacode_settings.exists(), ".gigacode/settings.json must exist for local GigaCode operation"
    
    # Check files are NOT tracked by Git
    result = subprocess.run(
        ["git", "ls-files", str(gigacode_settings.relative_to(REPO))],
        capture_output=True,
        text=True,
        cwd=REPO
    )
    assert result.stdout.strip() == "", f"{gigacode_settings} must not be tracked by Git"
    
    # Check .gitignore contains the entries
    gitignore_path = REPO / ".gitignore"
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text()
        assert ".gigacode/settings.json" in gitignore_content, ".gigacode/settings.json must be in .gitignore"
    
    # Check .gigacode/settings.json.orig is also handled
    if gigacode_settings_orig.exists():
        result = subprocess.run(
            ["git", "ls-files", str(gigacode_settings_orig.relative_to(REPO))],
            capture_output=True,
            text=True,
            cwd=REPO
        )
        assert result.stdout.strip() == "", f"{gigacode_settings_orig} must not be tracked by Git"

    # Check for actual generated artifacts in tracked files
    generated_suffixes = {".bak", ".backup", ".broken", ".iml", ".zip", ".tgz"}
    offenders = []
    for path in REPO.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", "node_modules", "dist", "build", ".pytest_cache", "__pycache__"} for part in path.parts):
            continue
        if path.suffix.casefold() in generated_suffixes:
            # Check if file is tracked by Git
            result = subprocess.run(
                ["git", "ls-files", str(path.relative_to(REPO))],
                capture_output=True,
                text=True,
                cwd=REPO
            )
            if result.stdout.strip():
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
