"""Integration tests for RealLLMClient with SBT Hub AI (QwenCoder)."""

import asyncio
import pytest

from po_agent.llm.client import LLMMessage
from po_agent.llm.real import RealLLMClient


class TestRealLLMClient:
    """Integration tests for real LLM client (QwenCoder)."""

    @pytest.fixture
    def client(self):
        """Create real LLM client for testing."""
        return RealLLMClient()

    @pytest.mark.asyncio
    async def test_real_llm_completion(self, client):
        """Test real LLM completion with QwenCoder."""
        messages = [
            LLMMessage(
                role="system",
                content="You are a helpful assistant. Always respond in English.",
            ),
            LLMMessage(
                role="user",
                content="Say hello in one word.",
            ),
        ]

        response = await client.complete(messages)

        assert response.choices is not None
        assert len(response.choices) > 0
        assert response.choices[0].message.role == "assistant"
        assert len(response.choices[0].message.content) > 0

    @pytest.mark.asyncio
    async def test_real_llm_usage(self, client):
        """Test that real LLM returns usage info."""
        messages = [
            LLMMessage(
                role="user",
                content="What is 2+2?",
            ),
        ]

        response = await client.complete(messages)

        assert response.usage is not None
        assert response.usage.prompt_tokens >= 0
        assert response.usage.completion_tokens >= 0

    @pytest.mark.asyncio
    async def test_real_llm_stream(self, client):
        """Test real LLM streaming."""
        messages = [
            LLMMessage(
                role="user",
                content="Count from 1 to 5, each on new line.",
            ),
        ]

        chunks = []
        async for chunk in client.stream(messages):
            chunks.append(chunk)
            assert chunk.choices is not None

        # Should have multiple chunks
        assert len(chunks) > 1

    @pytest.mark.asyncio
    async def test_real_llm_close(self, client):
        """Test client close method."""
        await client.close()  # Should not raise
