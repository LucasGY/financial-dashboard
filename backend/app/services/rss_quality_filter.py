from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class QualityDecision:
    should_ingest: bool
    score: int
    reason: str


PROMOTIONAL_PATTERNS = (
    "discount code",
    "subscribe now",
    "join my course",
    "course bundle",
    "limited discount",
    "use code",
)

LOW_SIGNAL_PATTERNS = (
    r"^(re\s+@\w+\s+(lol|lmao|wow|nice|this|same|true|wild|yep|nope)[\s!.😂🫡]*)+$",
    r"^rt\s+@\w+\s*$",
    r"^(lol|lmao|wow|nice|big if true|this is wild)[\s!.😂🫡]*$",
)


def evaluate_rss_item(
    *,
    domain: str,
    source_platform: str,
    source_type: str,
    title: str,
    summary: str,
    entity_ids: list[str],
    event_tags: list[str],
    source_url: str | None,
) -> QualityDecision:
    text = f"{title} {summary}".strip()
    lowered = text.lower()
    if any(pattern in lowered for pattern in PROMOTIONAL_PATTERNS):
        return QualityDecision(False, 0, "promotional")
    if _effective_length(text) < 20 or any(re.match(pattern, lowered) for pattern in LOW_SIGNAL_PATTERNS):
        return QualityDecision(False, 0, "low_signal")

    return QualityDecision(True, 0, "accepted")


def _effective_length(value: str) -> int:
    return len(re.sub(r"\s+", "", value))
