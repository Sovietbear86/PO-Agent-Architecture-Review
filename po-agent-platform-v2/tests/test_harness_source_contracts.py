from pathlib import Path

from po_agent.harness.source_contracts import SourceDependencyBundle, YamlTeamCompetencySource


def test_yaml_team_source_reads_declared_profile_without_inventing_competencies(tmp_path: Path):
    config = tmp_path / "team_members.yaml"
    config.write_text(
        """
members:
  - login: dev.one
    grade: 11
    products: [DTMS]
    professional_profile: Go-разработчик DataMarts
    competencies: {}
  - login: qa.one
    products: [DTMS]
    professional_profile: Инженер тестирования
    competencies:
      functional_testing: true
      java: false
""".strip(),
        encoding="utf-8",
    )

    source = YamlTeamCompetencySource(config)
    profiles = source.list_profiles()

    assert [p.login for p in profiles] == ["dev.one", "qa.one"]
    assert profiles[0].professional_profile == "Go-разработчик DataMarts"
    assert profiles[0].competencies == ()
    assert profiles[1].competencies == ("functional_testing",)
    assert source.has_declared_profiles() is True


def test_missing_team_config_is_not_misreported_as_empty_real_team(tmp_path: Path):
    source = YamlTeamCompetencySource(tmp_path / "missing.yaml")
    assert source.list_profiles() == ()
    assert source.has_declared_profiles() is False


def test_dependency_bundle_advertises_only_injected_source_facts(tmp_path: Path):
    team = YamlTeamCompetencySource(tmp_path / "team.yaml")
    bundle = SourceDependencyBundle(team_competencies=team)
    assert bundle.facts == frozenset({"team_competencies"})
