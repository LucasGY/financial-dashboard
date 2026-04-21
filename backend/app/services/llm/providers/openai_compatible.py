from __future__ import annotations

import httpx

from app.core.config import Settings
from app.core.errors import DataUnavailableError
from app.services.llm.providers.base import LLMMessage


class OpenAICompatibleProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def is_configured(self) -> bool:
        return bool(self._settings.llm_api_key)

    def generate(self, messages: list[LLMMessage], temperature: float = 0.0) -> str:
        if not self.is_configured():
            raise DataUnavailableError("llm provider is not configured")

        response = httpx.post(
            f"{self._settings.llm_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._settings.llm_model,
                "temperature": temperature,
                "messages": [{"role": item.role, "content": item.content} for item in messages],
            },
            timeout=20.0,
        )
        if response.status_code >= 400:
            raise DataUnavailableError("llm provider request failed")
        payload = response.json()
        choices = payload.get("choices") or []
        if not choices:
            raise DataUnavailableError("llm provider returned no choices")
        return str(choices[0]["message"]["content"])
