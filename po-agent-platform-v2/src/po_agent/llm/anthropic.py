"""Anthropic LLM implementation for PO Agent Platform v2."""

import os
import httpx
from typing import Any, AsyncGenerator, Optional

from po_agent.llm.client import (
    LLMClient,
    LLMMessage,
    LLMResponse,
    LLMUsage,
)


class AnthropicLLMClient(LLMClient):
    """Anthropic LLM client implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "claude-3-5-sonnet-20241022",
    ):
        """Initialize Anthropic client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            base_url: Base URL for Anthropic API (defaults to https://api.anthropic.com/v1)
            default_model: Default model to use
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url or "https://api.anthropic.com/v1"
        self.default_model = default_model

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not provided and not set in environment")

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
                "anthropic-dangerous-allow-cors-from": "*",
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
        """Generate a completion from Anthropic."""
        # Anthropic requires system message as separate parameter
        system = ""
        anthropic_messages = []

        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        payload = {
            "messages": anthropic_messages,
            "model": model or self.default_model,
            "temperature": temperature,
        }

        if system:
            payload["system"] = system

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        if stop:
            payload["stop_sequences"] = stop

        payload.update(kwargs)

        response = await self._client.post("/messages", json=payload)
        response.raise_for_status()

        data = response.json()

        # Extract usage if available
        usage = None
        if "usage" in data:
            usage = LLMUsage(
                prompt_tokens=data["usage"].get("input_tokens", 0),
                completion_tokens=data["usage"].get("output_tokens", 0),
                total_tokens=data["usage"].get("input_tokens", 0) + data["usage"].get("output_tokens", 0),
            )

        # Extract choices
        choices = []
        for content in data.get("content", []):
            if content.get("type") == "text":
                choices.append({
                    "message": {
                        "role": "assistant",
                        "content": content.get("text", ""),
                    },
                    "finish_reason": data.get("stop_reason"),
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
        """Stream completion chunks from Anthropic."""
        # Anthropic requires system message as separate parameter
        system = ""
        anthropic_messages = []

        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        payload = {
            "messages": anthropic_messages,
            "model": model or self.default_model,
            "temperature": temperature,
            "stream": True,
        }

        if system:
            payload["system"] = system

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        if stop:
            payload["stop_sequences"] = stop

        payload.update(kwargs)

        async with self._client.stream("POST", "/messages", json=payload) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line:
                    continue

                # Anthropic streams data with "data: " prefix
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

        Note: Anthropic doesn't provide a direct token counting endpoint.
        This is a rough estimation.
        """
        # Simple heuristic: ~4 chars per token on average
        return max(1, len(text) // 4)

    async def close(self) -> None:
        """Close client and release resources."""
        await self._client.aclose()

    def _parse_chunk(self, data: str) -> Optional[LLMResponse]:
        """Parse a chunk from Anthropic streaming response."""
        import json

        try:
            chunk = json.loads(data)

            if chunk.get("type") == "content_block_delta":
                return LLMResponse(
                    choices=[{
                        "message": {
                            "role": "assistant",
                            "content": chunk.get("delta", {}).get("text", ""),
                        },
                        "finish_reason": None,
                    }],
                    model=chunk.get("model"),
                    id=chunk.get("id"),
                )

            if chunk.get("type") == "message_delta":
                usage = None
                if "usage" in chunk:
                    usage = LLMUsage(
                        prompt_tokens=chunk["usage"].get("input_tokens", 0),
                        completion_tokens=chunk["usage"].get("output_tokens", 0),
                        total_tokens=chunk["usage"].get("input_tokens", 0) + chunk["usage"].get("output_tokens", 0),
                    )

                return LLMResponse(
                    choices=[{
                        "message": {
                            "role": "assistant",
                            "content": "",
                        },
                        "finish_reason": chunk.get("delta", {}).get("stop_reason"),
                    }],
                    usage=usage,
                    model=chunk.get("model"),
                    id=chunk.get("id"),
                )

            return None

        except (json.JSONDecodeError, KeyError):
            return None
