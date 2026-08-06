def score_candidate(member: dict, required: dict, current_wip: int = 0) -> dict:
    competencies = member.get("competencies", {})
    ratios = []
    for name, required_level in required.items():
        actual = competencies.get(name, 0)
        ratios.append(min(actual / max(required_level, 1), 1.0))

    competency_score = sum(ratios) / len(ratios) if ratios else 0
    allocation = member.get("allocation_percent", 100) / 100
    max_wip = member.get("planning", {}).get("recommended_max_wip", 3)
    load_factor = max(0.0, 1 - current_wip / max(max_wip, 1))

    return {
        "member_id": member["id"],
        "score": round(0.7 * competency_score + 0.2 * allocation + 0.1 * load_factor, 3),
        "warning": "WIP limit reached" if current_wip >= max_wip else None,
    }
