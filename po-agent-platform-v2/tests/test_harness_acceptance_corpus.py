from pathlib import Path

import pytest
import yaml

from po_agent.harness import HarnessRequest, ResponseStatus
from po_agent.harness.runtime_factory import build_runtime_bundle
from po_agent.harness.skill_catalog import SKILL_CATALOG


CORPUS = Path(__file__).parent / "corpus" / "harness_acceptance_corpus.yaml"


def load_cases():
    data = yaml.safe_load(CORPUS.read_text(encoding="utf-8"))
    return data, data["cases"]


def test_acceptance_corpus_covers_every_canonical_skill_exactly_once():
    data, cases = load_cases()
    expected = {entry.id for entry in SKILL_CATALOG}
    actual = [case["skill"] for case in cases]

    assert data["schema_version"] == 1
    assert len(actual) == 54
    assert len(set(actual)) == 54
    assert set(actual) == expected
    assert all(len(case["phrases"]) >= data["rules"]["min_phrases_per_skill"] for case in cases)


def test_every_corpus_case_has_natural_language_variation_and_source_contract():
    data, cases = load_cases()
    for case in cases:
        assert case["phrases"]
        assert all(isinstance(p, str) and p.strip() for p in case["phrases"])
        # The corpus is the input set for Qwen semantic acceptance, not a list
        # of regex phrases the fallback router must memorize.
        assert len({p.casefold() for p in case["phrases"]}) >= 2
        if case.get("requires_fact"):
            assert isinstance(case["requires_fact"], str)
    assert data["rules"]["min_phrases_per_skill"] >= 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "skill"),
    [
        ("Покажи WMB-102", "task-lookup"),
        ("Найди login", "task-search"),
        ("Покажи задачи спринта WMB-SPRNT-1", "task-search-sprint"),
        ("Готовность релиза WMB-2024-Q3", "release-progress"),
        ("Покажи историю WMB-101", "task-history"),
    ],
)
async def test_conservative_fallback_keeps_small_structural_safety_path(query, skill):
    """Fallback is deliberately small; Qwen owns broad language understanding."""
    bundle = build_runtime_bundle("fake")
    response = await bundle.runtime.process(HarnessRequest(query=query, session_id=f"fallback-{skill}"))
    assert response.status in {ResponseStatus.COMPLETED, ResponseStatus.PARTIAL}
    assert response.skill_id == skill
    assert response.trace_id


def test_legacy_language_corpus_keeps_high_value_old_agent_phrases():
    data, _ = load_cases()
    queries = {case["query"] for case in data["legacy_language_cases"]}
    assert "задачи Гаранина в спринте OLP-SPRNT-3" in queries
    assert "скорость команды" in queries
    assert "когда закончится спринт" in queries
    assert any("PDF-вложениями" in query for query in queries)
    assert any("последние 30 комментариев" in query for query in queries)
