import pytest

from po_agent.adapters.task_api import AS21CapabilityUnavailable
from po_agent.harness.sprint_intelligence import SprintIntelligenceCapabilities


@pytest.mark.asyncio
async def test_sprint_intelligence_requires_sprint_id_before_adapter_call():
    capability = SprintIntelligenceCapabilities(adapter=object())

    with pytest.raises(AS21CapabilityUnavailable, match="sprint_id is required"):
        await capability._tasks({})


@pytest.mark.asyncio
async def test_sprint_intelligence_normalizes_sprint_id_before_read():
    class Adapter:
        def __init__(self):
            self.sprint_id = None

        async def get_sprint_tasks(self, sprint_id):
            self.sprint_id = sprint_id
            return []

    adapter = Adapter()
    capability = SprintIntelligenceCapabilities(adapter=adapter)

    sprint_id, tasks = await capability._tasks({"sprint_id": " dms-sprnt-2 "})

    assert sprint_id == "DMS-SPRNT-2"
    assert adapter.sprint_id == "DMS-SPRNT-2"
    assert tasks == []
