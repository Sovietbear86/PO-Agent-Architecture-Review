"""LLM Client Abstraction for PO Agent Platform v2.

This module provides a provider-agnostic interface for LLM interactions.
Supports OpenAI, Anthropic, and other providers via adapter pattern.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Optional

from pydantic import BaseModel


class PromptVersionInfo(BaseModel):
    """Information about prompt version."""
    prompt_name: str
    prompt_version: str
    model_used: Optional[str] = None
    timestamp: str


class LLMMessage(BaseModel):
    """Message in LLM conversation."""
    role: str  # "system", "user", "assistant"
    content: str


class LLMChoice(BaseModel):
    """Choice from LLM response."""
    message: LLMMessage
    finish_reason: Optional[str] = None


class LLMUsage(BaseModel):
    """Token usage statistics."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMResponse(BaseModel):
    """Response from LLM."""
    choices: list[LLMChoice]
    usage: Optional[LLMUsage] = None
    model: Optional[str] = None
    id: Optional[str] = None


class LLMClient(ABC):
    """Abstract base class for LLM clients.

    Provides a provider-agnostic interface for LLM interactions.
    """

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion from the LLM.

        Args:
            messages: List of conversation messages
            model: Model name to use (optional, uses default if not specified)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            stop: Stop sequences
            **kwargs: Additional provider-specific arguments

        Returns:
            LLMResponse with choices and usage
        """

    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[LLMResponse, None]:
        """Stream completion chunks from the LLM.

        Args:
            messages: List of conversation messages
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stop: Stop sequences
            **kwargs: Additional provider-specific arguments

        Yields:
            LLMResponse chunks
        """

    @abstractmethod
    async def count_tokens(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for
            model: Model name (affects tokenization)

        Returns:
            Number of tokens
        """

    @abstractmethod
    async def close(self) -> None:
        """Close client and release resources."""


class PromptVersionClient:
    """Client wrapper that tracks prompt versions.

    Wraps an existing LLM client and records prompt version info
    for each request using the VersionRegistry.
    """

    def __init__(
        self,
        inner_client: "LLMClient",
        version_registry: "VersionRegistry",
    ):
        """Initialize prompt version client.

        Args:
            inner_client: Wrapped LLM client
            version_registry: Version registry for prompt tracking
        """
        self.inner_client = inner_client
        self.version_registry = version_registry

    async def complete(
        self,
        messages: list[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Complete with prompt version tracking."""
        # Get current prompt version
        prompt_version = self.version_registry.get_active_version(
            component_type="prompt",
            component_name="default",
        )
        if prompt_version:
            kwargs["_prompt_version"] = str(prompt_version.version)

        return await self.inner_client.complete(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
            **kwargs,
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
        """Stream with prompt version tracking."""
        async for chunk in self.inner_client.stream(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
            **kwargs,
        ):
            yield chunk

    async def count_tokens(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> int:
        """Count tokens."""
        return await self.inner_client.count_tokens(text=text, model=model)

    async def close(self) -> None:
        """Close wrapped client."""
        await self.inner_client.close()



__all__ = [
    "LLMMessage",
    "LLMChoice",
    "LLMUsage",
    "LLMResponse",
    "LLMClient",
    "PromptVersionInfo",
    "PromptVersionClient",
]
