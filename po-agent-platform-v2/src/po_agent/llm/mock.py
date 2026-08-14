"""Mock LLM implementation for testing purposes."""

import asyncio
from typing import Any, AsyncGenerator, Optional

from po_agent.llm.client import (
    LLMClient,
    LLMMessage,
    LLMResponse,
    LLMUsage,
)


class MockLLMClient(LLMClient):
    """Mock LLM client for testing without real API calls.

    Returns deterministic responses for testing purposes.
    """

    def __init__(
        self,
        default_model: str = "mock-model",
        response_text: str = "This is a mock response",
    ):
        """Initialize mock client.

        Args:
            default_model: Default model name
            response_text: Default response text
        """
        self.default_model = default_model
        self.response_text = response_text
        self._call_count = 0

    async def complete(
        self,
        messages: list[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a mock completion."""
        self._call_count += 1

        return LLMResponse(
            choices=[{
                "message": {
                    "role": "assistant",
                    "content": self.response_text,
                },
                "finish_reason": "stop",
            }],
            usage=LLMUsage(
                prompt_tokens=len(" ".join(m.content for m in messages)) // 4,
                completion_tokens=len(self.response_text) // 4,
                total_tokens=0,
            ),
            model=model or self.default_model,
            id=f"mock-{self._call_count}",
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[LLMResponse, None]:
        """Stream mock completion chunks."""
        chunk_size = 5  # Split response into chunks of 5 characters

        for i in range(0, len(self.response_text), chunk_size):
            chunk = self.response_text[i:i + chunk_size]
            yield LLMResponse(
                choices=[{
                    "message": {
                        "role": "assistant",
                        "content": chunk,
                    },
                    "finish_reason": None,
                }],
                model=model or self.default_model,
                id="mock-stream",
            )
            await asyncio.sleep(0.01)  # Simulate network delay

        # Final chunk with finish_reason
        yield LLMResponse(
            choices=[{
                "message": {
                    "role": "assistant",
                    "content": "",
                },
                "finish_reason": "stop",
            }],
            usage=LLMUsage(
                prompt_tokens=len(" ".join(m.content for m in messages)) // 4,
                completion_tokens=len(self.response_text) // 4,
                total_tokens=0,
            ),
            model=model or self.default_model,
            id="mock-stream-done",
        )

    async def count_tokens(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> int:
        """Count tokens (mock implementation)."""
        return max(1, len(text) // 4)

    async def close(self) -> None:
        """Close mock client (no-op)."""
        pass

    def get_call_count(self) -> int:
        """Get number of calls made to the mock."""
        return self._call_count

    def reset_call_count(self) -> None:
        """Reset call counter."""
        self._call_count = 0
