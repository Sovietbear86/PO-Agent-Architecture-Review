"""Real LLM client using SBT Hub AI (QwenCoder) for PO Agent Platform v2."""

import os
import httpx
from typing import Any, AsyncGenerator, Optional

from po_agent.llm.client import (
    LLMClient,
    LLMMessage,
    LLMResponse,
    LLMUsage,
)


class RealLLMClient(LLMClient):
    """Real LLM client using SBT Hub AI API (QwenCoder/Qwen3-Coder-Next).

    Connects to the same LLM service used by s21-team-performance-agent.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
    ):
        """Initialize real LLM client.

        Args:
            api_key: API key for SBT Hub AI (defaults to env var or file)
            base_url: Base URL for SBT Hub AI API
            model: Model name to use (default: Qwen/Qwen3-Coder-Next)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        if not self.api_key:
            # Try environment variable
            self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            # Try to read from file
            try:
                with open("/Users/kalachanov.v.v/.config/openai/api_key", "r") as f:
                    self.api_key = f.read().strip()
            except:
                pass

        if not self.api_key:
            raise ValueError("API key not provided and not found in environment or file")

        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.ai.sbt/openai/v1")
        self.model = model or os.getenv("OPENAI_MODEL", "Qwen/Qwen3-Coder-Next")
        self.timeout = timeout

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout),
            verify=False,  # Self-signed cert
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
        """Generate a completion from the real LLM."""
        payload = {
            "messages": [m.model_dump() for m in messages],
            "model": model or self.model,
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
        """Stream completion chunks from the real LLM."""
        payload = {
            "messages": [m.model_dump() for m in messages],
            "model": model or self.model,
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

                # OpenAI-compatible streaming with "data: " prefix
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

        Note: Uses a simple heuristic since direct endpoint is not available.
        """
        # Simple heuristic: ~4 chars per token on average
        return max(1, len(text) // 4)

    async def close(self) -> None:
        """Close client and release resources."""
        await self._client.aclose()

    def _parse_chunk(self, data: str) -> Optional[LLMResponse]:
        """Parse a chunk from streaming response."""
        import json

        try:
            chunk = json.loads(data)

            # Extract usage if available
            usage = None
            if "usage" in chunk:
                usage = LLMUsage(
                    prompt_tokens=chunk["usage"].get("prompt_tokens", 0),
                    completion_tokens=chunk["usage"].get("completion_tokens", 0),
                    total_tokens=chunk["usage"].get("total_tokens", 0),
                )

            # Extract choices
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
