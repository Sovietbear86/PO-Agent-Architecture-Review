"""OpenAI LLM implementation for PO Agent Platform v2."""

import os
import httpx
from typing import Any, AsyncGenerator, Optional

from po_agent.llm.client import (
    LLMClient,
    LLMMessage,
    LLMResponse,
    LLMUsage,
)


class OpenAILLMClient(LLMClient):
    """OpenAI LLM client implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "gpt-4o-mini",
    ):
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            base_url: Base URL for OpenAI API (defaults to https://api.openai.com/v1)
            default_model: Default model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or "https://api.openai.com/v1"
        self.default_model = default_model

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not provided and not set in environment")

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def complete(
        self,
        messages: list[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion from OpenAI."""
        payload = {
            "messages": [m.model_dump() for m in messages],
            "model": model or self.default_model,
            "temperature": temperature,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        if stop:
            payload["stop"] = stop

        payload.update(kwargs)

        response = await self._client.post("/chat/completions", json=payload)
        response.raise_for_status()

        data = response.json()

        # Extract usage if available
        usage = None
        if "usage" in data:
            usage = LLMUsage(
                prompt_tokens=data["usage"].get("prompt_tokens", 0),
                completion_tokens=data["usage"].get("completion_tokens", 0),
                total_tokens=data["usage"].get("total_tokens", 0),
            )

        # Extract choices
        choices = []
        for choice in data.get("choices", []):
            msg = choice.get("message", {})
            choices.append({
                "message": {
                    "role": msg.get("role", "assistant"),
                    "content": msg.get("content", ""),
                },
                "finish_reason": choice.get("finish_reason"),
            })

        return LLMResponse(
            choices=choices,
            usage=usage,
            model=data.get("model"),
            id=data.get("id"),
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
        """Stream completion chunks from OpenAI."""
        payload = {
            "messages": [m.model_dump() for m in messages],
            "model": model or self.default_model,
            "temperature": temperature,
            "stream": True,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        if stop:
            payload["stop"] = stop

        payload.update(kwargs)

        async with self._client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line:
                    continue

                # OpenAI streams data with "data: " prefix
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix

                    if data == "[DONE]":
                        break

                    try:
                        chunk = self._parse_chunk(data)
                        if chunk:
                            yield chunk
                    except Exception:
                        continue

    async def count_tokens(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> int:
        """Count tokens in text.

        Note: OpenAI doesn't provide a direct token counting endpoint.
        This is a rough estimation using tiktoken-like heuristic.
        """
        # Simple heuristic: ~4 chars per token on average
        return max(1, len(text) // 4)

    async def close(self) -> None:
        """Close client and release resources."""
        await self._client.aclose()

    def _parse_chunk(self, data: str) -> Optional[LLMResponse]:
        """Parse a chunk from OpenAI streaming response."""
        import json

        try:
            chunk = json.loads(data)

            # Extract usage from delta if available
            usage = None
            if "usage" in chunk:
                usage = LLMUsage(
                    prompt_tokens=chunk["usage"].get("prompt_tokens", 0),
                    completion_tokens=chunk["usage"].get("completion_tokens", 0),
                    total_tokens=chunk["usage"].get("total_tokens", 0),
                )

            # Extract choice
            choices = []
            for choice in chunk.get("choices", []):
                delta = choice.get("delta", {})
                if delta:  # Non-empty delta
                    choices.append({
                        "message": {
                            "role": delta.get("role", "assistant"),
                            "content": delta.get("content", ""),
                        },
                        "finish_reason": choice.get("finish_reason"),
                    })

            if choices:
                return LLMResponse(
                    choices=choices,
                    usage=usage,
                    model=chunk.get("model"),
                    id=chunk.get("id"),
                )
            return None

        except (json.JSONDecodeError, KeyError):
            return None
