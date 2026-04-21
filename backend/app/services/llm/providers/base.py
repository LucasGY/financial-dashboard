from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


class LLMProvider(Protocol):
    def is_configured(self) -> bool: ...

    def generate(self, messages: list[LLMMessage], temperature: float = 0.0) -> str: ...
