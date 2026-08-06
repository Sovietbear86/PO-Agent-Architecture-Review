#!/usr/bin/env python
"""Test integration between Team Performance Agent and SWTR Adapter."""

from __future__ import annotations

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from s21_agent.connectors.s21_swtr_adapter import SWTRAdapter
from s21_team_performance.services.task_service import TaskService, load_team_members
from s21_team_performance.skills.sprint_health import SprintHealthSkill
from s21_team_performance.skills.velocity_analysis import VelocityAnalysisSkill
from s21_team_performance.skills.flow_metrics import FlowMetricsSkill
from s21_team_performance.skills.workload_balance import WorkloadBalanceSkill


async def test_swtr_adapter():
    """Test SWTR Adapter directly."""
    print("=" * 60)
    print("Testing SWTR Adapter")
    print("=" * 60)

    adapter = SWTRAdapter(api_port=8003)

    # Test search with assignee filter
    print("\n1. Searching tasks for Kalachanov.V.V...")
    tasks = adapter.search_tasks("", {"assignee": "Kalachanov.V.V"})
    print(f"   Found {len(tasks)} tasks")

    if tasks:
        print(f"   Sample task: {tasks[0].title}")
        print(f"   Task status: {tasks[0].status}")
        print(f"   Task assignee: {tasks[0].assignee}")

    print("✅ SWTR Adapter test completed")


async def test_task_service():
    """Test Task Service."""
    print("\n" + "=" * 60)
    print("Testing Task Service")
    print("=" * 60)

    service = TaskService(api_port=8003)

    # Test loading team members
    print("\n1. Loading team members...")
    members = load_team_members()
    print(f"   Found {len(members)} team members")

    # Test fetch tasks by assignee
    print("\n2. Fetching tasks for Kalachanov.V.V...")
    tasks = await service.fetch_tasks_by_assignee("Kalachanov.V.V")
    print(f"   Found {len(tasks)} tasks")

    # Test calculate flow metrics
    print("\n3. Calculating flow metrics...")
    members_logins = [m.get("login") for m in members[:5]]  # First 5 members
    flow_metrics = await service.calculate_flow_metrics(period_days=30)
    print(f"   Throughput: {flow_metrics.throughput} tasks")
    print(f"   Avg Cycle Time: {flow_metrics.avg_cycle_time} days")
    print(f"   Avg Lead Time: {flow_metrics.avg_lead_time} days")
    print(f"   Avg WIP: {flow_metrics.avg_wip}")
    print(f"   Flow Efficiency: {flow_metrics.flow_efficiency:.1%}")

    print("✅ Task Service test completed")


async def test_skills():
    """Test individual skills."""
    print("\n" + "=" * 60)
    print("Testing Skills with Real Data")
    print("=" * 60)

    # Test Sprint Health Skill
    print("\n1. Sprint Health Skill...")
    skill = SprintHealthSkill(api_port=8003)
    # Use all team members to find tasks
    all_members = [m.get("login") for m in load_team_members()]
    result = await skill.analyze(
        sprint_id="SPRINT-2026-01",
        period_days=30,
        team_members=all_members[:5]  # First 5 members
    )
    print(f"   Status: {result.status}")
    print(f"   Findings count: {len(result.findings)}")
    print(f"   Risks count: {len(result.risks)}")

    # Test Velocity Analysis Skill
    print("\n2. Velocity Analysis Skill...")
    velocity_skill = VelocityAnalysisSkill(api_port=8003)
    velocity_result = await velocity_skill.analyze(
        period_days=30,
        team_members=all_members[:5]
    )
    print(f"   Status: {velocity_result.status}")
    print(f"   Findings: {velocity_result.findings[0] if velocity_result.findings else 'N/A'}")

    # Test Flow Metrics Skill
    print("\n3. Flow Metrics Skill...")
    flow_skill = FlowMetricsSkill(api_port=8003)
    flow_result = await flow_skill.analyze(
        period_days=30,
        team_members=all_members[:5]
    )
    print(f"   Status: {flow_result.status}")
    print(f"   Findings: {flow_result.findings[0] if flow_result.findings else 'N/A'}")
    print(f"   Risk: {flow_result.risks[0] if flow_result.risks else 'N/A'}")

    # Test Workload Balance Skill
    print("\n4. Workload Balance Skill...")
    workload_skill = WorkloadBalanceSkill(api_port=8003)
    workload_result = await workload_skill.analyze(
        period_days=30,
        team_members=all_members[:5]
    )
    print(f"   Status: {workload_result.status}")
    print(f"   Total tasks: {workload_result.findings[0] if workload_result.findings else 'N/A'}")

    print("✅ Skills test completed")


async def main():
    """Run all tests."""
    print("🚀 Team Performance Agent - SWTR Integration Test")
    print("=" * 60)

    try:
        await test_swtr_adapter()
        await test_task_service()
        await test_skills()

        print("\n" + "=" * 60)
        print("🎉 All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
