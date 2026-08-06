"""LLM Client for task analysis - uses SBT Hub AI API via OpenAI-compatible endpoint."""
from __future__ import annotations

import json
import os
from typing import Optional

from s21_agent.config import settings


class LLMClient:
    """Client for SBT Hub AI API (OpenAI-compatible endpoint)."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # Use Hub AI API endpoint
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.timeout = settings.openai_timeout_seconds
        self.base_url = settings.openai_base_url or "https://api.ai.sbt/openai/v1"
        self._gigachat_client = None

    def _get_gigachat_client(self):
        """Get GigaChat client instance."""
        if self._gigachat_client is None and self.api_key:
            try:
                from gigachat import GigaChat
                self._gigachat_client = GigaChat(
                    credentials=self.api_key,
                    verify_ssl_certs=False,
                    timeout=self.timeout
                )
            except Exception:
                pass
        return self._gigachat_client

    def analyze_task(self, task_title: str, task_description: str, instructions: str, history: Optional[list] = None) -> str:
        """
        Analyze task using SBT Hub AI API (OpenAI-compatible).

        Args:
            task_title: Task title
            task_description: Task description
            instructions: Instructions for analysis
            history: Conversation history for context (optional)

        Returns:
            LLM analysis result
        """
        import httpx
        import json

        system_prompt = """You are a product owner assistant. Analyze task descriptions and extract key information.

Follow instructions carefully. If the task doesn't contain the requested information, say so clearly.
Keep answers concise but complete in Russian."""

        # Build user prompt with history context
        user_prompt = f"""Task Title: {task_title}

Task Description:
{task_description}

Instructions: {instructions}"""

        # Add conversation history to prompt if available
        if history and len(history) > 0:
            history_text = "\n\nPrevious conversation:\n" + "\n".join(
                [f"- {msg.get('content', '')}" for msg in history[-5:]]
            )
            user_prompt += history_text

        # Try SBT Hub AI API first (OpenAI-compatible)
        if self.api_key:
            try:
                with httpx.Client(timeout=self.timeout, verify=False) as client:
                    response = client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            "temperature": 0.3,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
            except httpx.HTTPError as e:
                print(f"SBT Hub AI API error: {e}")
                # Fallback to GigaChat
                pass

        # Try GigaChat
        gigachat = self._get_gigachat_client()
        if gigachat:
            try:
                response = gigachat.chat(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"GigaChat failed: {e}")

        # Fallback to simple extraction
        return self._fallback_analysis(task_title, task_description, instructions)

    def _fallback_analysis(self, task_title: str, task_description: str, instructions: str) -> str:
        """Fallback to rule-based analysis if no API available."""
        instructions_lower = instructions.lower()
        
        if "дод" in instructions_lower or "критерии" in instructions_lower:
            desc_lower = task_description.lower()
            dod_keywords = ["критерии", "приемка", "условия", "готово", "done", " acceptance"]
            has_dod = any(kw in desc_lower for kw in dod_keywords)
            
            if has_dod:
                return "Definition of Done найден в описании задачи. Проверьте наличие критериев приемки."
            else:
                return "Definition of Done не указан в задаче. Рекомендуется добавить критерии приемки."
        
        elif "суммариз" in instructions_lower or "ключевые" in instructions_lower:
            import re
            lines = task_description.split('\n')
            key_points = [l.strip() for l in lines if re.match(r'^\d+', l.strip())][:5]
            
            if key_points:
                return "Ключевые моменты: " + " | ".join(key_points[:3])
            return "Описание задачи не содержит структурированных пунктов."
        
        return "Анализ завершен. Для детального анализа настройте API ключ."

    def extract_dod(self, task_title: str, task_description: str) -> str:
        """Extract Definition of Done from task description."""
        instructions = """Extract the Definition of Done (DoD) from this task description.

Look for sections about:
1. Criteria for accepting the task as complete
2. Requirements that must be fulfilled before marking as done
3. Acceptance criteria or conditions of satisfaction

If DoD is explicitly labeled (e.g., "Definition of Done", "Критерии приемки", "DoD"), extract that section.
If DoD is embedded in the description, extract the relevant parts.
If no DoD exists, return "Definition of Done не указан в задаче".
"""

        return self.analyze_task(task_title, task_description, instructions)

    def summarize_task(self, task_title: str, task_description: str) -> str:
        """Generate a summary of the task with key points."""
        instructions = """Summarize this task providing:
1. Main goal/objective
2. Key actions required (numbered list)
3. Important deadlines or milestones
4. Key contacts or responsible persons
5. Definition of Done if present

Keep it concise but informative. Use Russian if the task is in Russian."""

        return self.analyze_task(task_title, task_description, instructions)

    def extract_intent(self, query: str) -> dict:
        """Extract intent and parameters from user query."""
        prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'extract_intent.md')
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                instructions = f.read()
        except:
            instructions = """Проанализируй запрос пользователя и извлеки намерение и параметры.
Верни JSON с полями: intent (sprint|my_tasks|search|unknown), assignee, search_terms."""

        return self.analyze_task_with_json_output(query, instructions)

    def analyze_task_with_json_output(self, content: str, instructions: str) -> dict:
        """Analyze content and return JSON output."""
        import httpx

        system_prompt = """Ты - assistant, который всегда возвращает данные в формате JSON.
Следуй инструкциям строго, возвращай только валидный JSON без дополнительного текста.
Если поле не применимо, используй null."""

        user_prompt = f"""Content: {content}

Instructions: {instructions}"""

        # Try SBT Hub AI API first
        if self.api_key:
            try:
                with httpx.Client(timeout=self.timeout, verify=False) as client:
                    response = client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            "temperature": 0.1,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    # Extract JSON from response
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        return json.loads(content[json_start:json_end])
                    return json.loads(content)
            except Exception as e:
                print(f"SBT Hub AI API error: {e}")
                pass

        # Fallback
        return {"intent": "unknown", "assignee": None, "search_terms": None}
