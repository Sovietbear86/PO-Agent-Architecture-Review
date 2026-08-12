"""Tests for LLM Client implementations."""

import asyncio

import pytest

from po_agent.llm.client import LLMClient, LLMMessage, LLMResponse
from po_agent.llm.mock import MockLLMClient


@pytest.fixture
def mock_client():
    """Create mock LLM client for testing."""
    return MockLLMClient()


class TestMockLLMClient:
    """Tests for MockLLMClient."""

    def test_initialization(self):
        """Test mock client initialization."""
        client = MockLLMClient()
        assert client is not None

    def test_initialization_with_params(self):
        """Test mock client with custom parameters."""
        client = MockLLMClient(
            default_model="custom-model",
            response_text="Custom response",
        )
        assert client is not None

    async def _test_complete(self, mock_client):
        """Test complete method."""
        messages = [
            LLMMessage(role="user", content="Hello"),
        ]

        response = await mock_client.complete(messages)

        assert isinstance(response, LLMResponse)
        assert len(response.choices) == 1
        assert response.choices[0].message.role == "assistant"
        assert "mock" in response.choices[0].message.content.lower()

    def test_complete(self, mock_client):
        """Test complete method (async wrapper)."""
        asyncio.run(self._test_complete(mock_client))

    async def _test_complete_with_model(self, mock_client):
        """Test complete method with custom model."""
        messages = [
            LLMMessage(role="user", content="Test"),
        ]

        response = await mock_client.complete(messages, model="custom-model")

        assert response.model == "custom-model"

    def test_complete_with_model(self, mock_client):
        """Test complete method with custom model (async wrapper)."""
        asyncio.run(self._test_complete_with_model(mock_client))

    async def _test_stream(self, mock_client):
        """Test stream method."""
        messages = [
            LLMMessage(role="user", content="Stream test"),
        ]

        chunks = []
        async for chunk in mock_client.stream(messages):
            chunks.append(chunk)

        assert len(chunks) > 0

    def test_stream(self, mock_client):
        """Test stream method (async wrapper)."""
        asyncio.run(self._test_stream(mock_client))

    async def _test_stream_with_model(self, mock_client):
        """Test stream method with custom model."""
        messages = [
            LLMMessage(role="user", content="Test"),
        ]

        async for chunk in mock_client.stream(messages, model="stream-model"):
            assert chunk.model == "stream-model"

    def test_stream_with_model(self, mock_client):
        """Test stream method with custom model (async wrapper)."""
        asyncio.run(self._test_stream_with_model(mock_client))

    async def _test_count_tokens(self, mock_client):
        """Test count_tokens method."""
        text = "This is a test message with multiple tokens."
        count = await mock_client.count_tokens(text)

        assert count > 0

    def test_count_tokens(self, mock_client):
        """Test count_tokens method (async wrapper)."""
        asyncio.run(self._test_count_tokens(mock_client))

    async def _test_close(self, mock_client):
        """Test close method."""
        await mock_client.close()  # Should not raise

    def test_close(self, mock_client):
        """Test close method (async wrapper)."""
        asyncio.run(self._test_close(mock_client))

    def test_get_call_count(self, mock_client):
        """Test get_call_count method."""
        assert mock_client.get_call_count() == 0

    async def _test_call_count_increments(self, mock_client):
        """Test that call count increments on complete."""
        messages = [
            LLMMessage(role="user", content="Test"),
        ]

        await mock_client.complete(messages)
        assert mock_client.get_call_count() == 1

    def test_call_count_increments(self, mock_client):
        """Test that call count increments on complete (async wrapper)."""
        asyncio.run(self._test_call_count_increments(mock_client))

    async def _test_reset_call_count(self, mock_client):
        """Test reset_call_count method."""
        messages = [
            LLMMessage(role="user", content="Test"),
        ]

        await mock_client.complete(messages)
        assert mock_client.get_call_count() == 1

        mock_client.reset_call_count()
        assert mock_client.get_call_count() == 0

    def test_reset_call_count(self, mock_client):
        """Test reset_call_count method (async wrapper)."""
        asyncio.run(self._test_reset_call_count(mock_client))

    async def _test_response_usage(self, mock_client):
        """Test that response includes usage info."""
        messages = [
            LLMMessage(role="user", content="Test message with tokens"),
        ]

        response = await mock_client.complete(messages)

        assert response.usage is not None
        assert response.usage.prompt_tokens >= 0
        assert response.usage.completion_tokens >= 0

    def test_response_usage(self, mock_client):
        """Test that response includes usage info (async wrapper)."""
        asyncio.run(self._test_response_usage(mock_client))


class TestLLMClientInterface:
    """Tests for LLMClient interface contract."""

    def test_mock_implements_interface(self, mock_client):
        """Test that mock client implements LLMClient interface."""
        assert isinstance(mock_client, LLMClient)