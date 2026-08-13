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


@pytest.mark.asyncio
async def test_first_canonical_phrase_routes_to_expected_skill_when_fake_source_is_ready():
    _, cases = load_cases()
    bundle = build_runtime_bundle("fake")
    available = set(bundle.readiness.available_facts)

    for case in cases:
        required = case.get("requires_fact")
        # snapshot/competency/timeline dependencies are intentionally injected
        # by their dedicated source-contract tests, not invented in FakeAS21.
        if required and required not in available:
            continue
        response = await bundle.runtime.process(
            HarnessRequest(query=case["phrases"][0], session_id=f"corpus-{case['skill']}")
        )
        assert response.status in {ResponseStatus.COMPLETED, ResponseStatus.PARTIAL}, (
            case["skill"], response.to_dict()
        )
        assert response.skill_id == case["skill"], (case["skill"], response.to_dict())
        assert response.trace_id
        assert response.skill_version
        assert bundle.runtime.history.get(response.trace_id) is not None


def test_legacy_language_corpus_keeps_high_value_old_agent_phrases():
    data, _ = load_cases()
    queries = {case["query"] for case in data["legacy_language_cases"]}
    assert "задачи Гаранина в спринте OLP-SPRNT-3" in queries
    assert "скорость команды" in queries
    assert "когда закончится спринт" in queries
    assert any("PDF-вложениями" in query for query in queries)
    assert any("последние 30 комментариев" in query for query in queries)
