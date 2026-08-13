"""Real OpenAI-compatible LLM client for SBT Hub AI / Qwen."""

import json
import os
from typing import Any, AsyncGenerator, Optional

import httpx

from po_agent.llm.client import LLMClient, LLMMessage, LLMResponse, LLMUsage


class RealLLMClient(LLMClient):
    """OpenAI-compatible client used by the semantic Harness layer."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
        verify: bool = True,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("LLM API key is not configured")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.ai.sbt/openai/v1")
        self.model = model or os.getenv("OPENAI_MODEL", "Qwen/Qwen3-Coder-Next")
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            timeout=httpx.Timeout(timeout),
            verify=verify,
        )

    async def complete(self, messages: list[LLMMessage], model: Optional[str] = None, temperature: float = 0.7,
                       max_tokens: Optional[int] = None, stop: Optional[list[str]] = None, **kwargs: Any) -> LLMResponse:
        payload: dict[str, Any] = {"messages": [m.model_dump() for m in messages], "model": model or self.model, "temperature": temperature}
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if stop:
            payload["stop"] = stop
        payload.update(kwargs)
        response = await self._client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        usage = None
        if isinstance(data.get("usage"), dict):
            usage = LLMUsage(
                prompt_tokens=data["usage"].get("prompt_tokens", 0),
                completion_tokens=data["usage"].get("completion_tokens", 0),
                total_tokens=data["usage"].get("total_tokens", 0),
            )
        choices = []
        for choice in data.get("choices", []):
            msg = choice.get("message", {})
            choices.append({"message": {"role": msg.get("role", "assistant"), "content": msg.get("content", "")}, "finish_reason": choice.get("finish_reason")})
        return LLMResponse(choices=choices, usage=usage, model=data.get("model"), id=data.get("id"))

    async def stream(self, messages: list[LLMMessage], model: Optional[str] = None, temperature: float = 0.7,
                     max_tokens: Optional[int] = None, stop: Optional[list[str]] = None, **kwargs: Any) -> AsyncGenerator[LLMResponse, None]:
        payload: dict[str, Any] = {"messages": [m.model_dump() for m in messages], "model": model or self.model, "temperature": temperature, "stream": True}
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if stop:
            payload["stop"] = stop
        payload.update(kwargs)
        async with self._client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                chunk = self._parse_chunk(data)
                if chunk:
                    yield chunk

    async def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        return max(1, len(text) // 4)

    async def close(self) -> None:
        await self._client.aclose()

    def _parse_chunk(self, data: str) -> Optional[LLMResponse]:
        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            return None
        choices = []
        for choice in chunk.get("choices", []):
            delta = choice.get("delta", {})
            if delta:
                choices.append({"message": {"role": delta.get("role", "assistant"), "content": delta.get("content", "")}, "finish_reason": choice.get("finish_reason")})
        if not choices:
            return None
        return LLMResponse(choices=choices, model=chunk.get("model"), id=chunk.get("id"))
