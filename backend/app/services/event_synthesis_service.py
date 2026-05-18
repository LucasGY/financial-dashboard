from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

from app.repositories.models import IntelligenceEventRow
from app.services.intelligence_taxonomy import ENTITY_ALIASES, ENTITY_DISPLAY
from app.services.llm.providers.base import LLMMessage, LLMProvider


AI_EVENT_TAGS = {"model_release", "product_tool_update", "industry", "paper_research", "tips_opinion"}
FINANCE_EVENT_TAGS = {"kol_opinion", "macro", "company_industry"}


@dataclass(frozen=True)
class SyntheticEvent:
    title: str
    title_zh: str
    summary: str
    summary_zh: str
    event_tag: str
    entity_ids: list[str]
    importance_score: int


class EventSynthesisService:
    def __init__(self, llm_provider: Optional[LLMProvider]) -> None:
        self._llm_provider = llm_provider

    def synthesize(self, source_item: dict) -> SyntheticEvent:
        fallback = self._fallback(source_item)
        if not self._llm_provider or not self._llm_provider.is_configured():
            return fallback
        try:
            raw = self._llm_provider.generate(
                self._messages(source_item),
                temperature=0.0,
                response_format={"type": "json_object"},
                max_tokens=2200,
            )
            payload = _parse_json_object(raw)
            event_tag = str(payload.get("event_tag") or "")
            if event_tag not in _allowed_tags(str(source_item["domain"])):
                return fallback
            title = _first_text(payload, "title_en", "title")
            title_zh = _first_text(payload, "title_zh")
            summary = _first_text(payload, "summary_en", "summary")
            summary_zh = _first_text(payload, "summary_zh", "tldr_zh")
            entity_ids = _filter_entity_ids_by_evidence(
                _normalize_entity_ids(payload.get("entity_ids")),
                [source_item],
                event_tag,
            )
            importance_score = _parse_llm_score(payload.get("importance_score"))
            if not title or not title_zh or not summary or not summary_zh:
                return fallback
            return SyntheticEvent(
                title=title[:240],
                title_zh=title_zh[:240],
                summary=summary[:900],
                summary_zh=summary_zh[:900],
                event_tag=event_tag,
                entity_ids=entity_ids,
                importance_score=max(0, min(100, importance_score)),
            )
        except Exception:
            return fallback

    def synthesize_events(self, source_items: list[dict]) -> list[tuple[list[dict], SyntheticEvent]]:
        if not source_items:
            return []
        fallback = [([item], self._fallback(item)) for item in source_items]
        if not self._llm_provider or not self._llm_provider.is_configured():
            return fallback
        try:
            raw = self._llm_provider.generate(
                self._batch_messages(source_items),
                temperature=0.0,
                response_format={"type": "json_object"},
                max_tokens=5000,
            )
            payload = _parse_json_object(raw)
            events = payload.get("events")
            if not isinstance(events, list):
                return []
            indexed = {str(item["external_id"]): item for item in source_items}
            groups: list[tuple[list[dict], SyntheticEvent]] = []
            used_ids: set[str] = set()
            domain = str(source_items[0]["domain"])
            for event in events:
                if not isinstance(event, dict):
                    continue
                source_ids = [str(source_id) for source_id in event.get("source_ids") or []]
                group_sources = [indexed[source_id] for source_id in source_ids if source_id in indexed and source_id not in used_ids]
                if not group_sources:
                    continue
                tag = str(event.get("event_tag") or "")
                title = _first_text(event, "title_en", "title")
                title_zh = _first_text(event, "title_zh")
                summary = _first_text(event, "summary_en", "summary")
                summary_zh = _first_text(event, "summary_zh", "tldr_zh")
                entity_ids = _filter_entity_ids_by_evidence(
                    _normalize_entity_ids(event.get("entity_ids")),
                    group_sources,
                    tag,
                )
                if tag not in _allowed_tags(domain) or not title or not title_zh or not summary or not summary_zh:
                    continue
                importance_score = _parse_llm_score(event.get("importance_score"))
                if importance_score is None:
                    continue
                groups.append(
                    (
                        group_sources,
                        SyntheticEvent(
                            title=title[:240],
                            title_zh=title_zh[:240],
                            summary=summary[:900],
                            summary_zh=summary_zh[:900],
                            event_tag=tag,
                            entity_ids=entity_ids,
                            importance_score=importance_score,
                        ),
                    )
                )
                used_ids.update(str(item["external_id"]) for item in group_sources)
            return groups
        except Exception:
            return []

    def match_existing_event(self, candidate_event: dict, existing_events: list[IntelligenceEventRow]) -> str | None:
        if not existing_events or not self._llm_provider or not self._llm_provider.is_configured():
            return None
        try:
            raw = self._llm_provider.generate(
                self._merge_messages(candidate_event, existing_events),
                temperature=0.0,
                response_format={"type": "json_object"},
                max_tokens=1600,
            )
            payload = _parse_json_object(raw)
            if str(payload.get("decision") or "").lower() != "merge":
                return None
            target_event_key = str(payload.get("target_event_key") or "")
            existing_keys = {event.event_key for event in existing_events}
            return target_event_key if target_event_key in existing_keys else None
        except Exception:
            return None

    def _messages(self, source_item: dict) -> list[LLMMessage]:
        domain = str(source_item["domain"])
        allowed_tags = ", ".join(sorted(_allowed_tags(domain)))
        entity_aliases = _entity_alias_prompt()
        return [
            LLMMessage(
                role="system",
                content=(
                    "You transform one cleaned RSS/social source into one concise intelligence event. "
                    "Primary sources define event facts; related_discussion sources provide commentary, reactions, or amplification. "
                    "Return only valid JSON object. Do not include markdown. The JSON must match this shape: "
                    '{"title_en":"...","title_zh":"...","summary_en":"...","summary_zh":"...",'
                    '"event_tag":"...","entity_ids":["..."],"importance_score":80}. '
                    f"Choose exactly one event_tag from: {allowed_tags}. "
                    f"Infer entity_ids from content using this canonical alias map: {entity_aliases}. "
                    "Entity ids must be primary subjects of the event. Do not tag an entity that is only cited as "
                    "background, related work, an example, a benchmark comparison, or inside a parenthetical list. "
                    "For paper_research, leave entity_ids empty unless the paper is specifically about that entity's "
                    "model, product, dataset, company, or system."
                ),
            ),
            LLMMessage(
                role="user",
                content=json.dumps(
                    {
                        "domain": domain,
                        "source_platform": source_item.get("source_platform"),
                        "source_type": source_item.get("source_type"),
                        "source_role": source_item.get("source_role") or "primary",
                        "raw_title": source_item.get("title"),
                        "raw_content": source_item.get("raw_content") or source_item.get("summary"),
                        "assets_count": len(source_item.get("assets") or []),
                        "quoted_url": source_item.get("quoted_url"),
                        "reposted_url": source_item.get("reposted_url"),
                        "reply_to_url": source_item.get("reply_to_url"),
                        "output_schema": {
                            "title_en": "short English event title, no clickbait",
                            "title_zh": "short Chinese event title",
                            "summary_en": "1-2 sentence English event summary, explain what changed and why it matters",
                            "summary_zh": "1-2 sentence Chinese event summary",
                            "event_tag": "one allowed tag",
                            "entity_ids": "canonical entity ids inferred from content",
                            "importance_score": "integer 0-100",
                        },
                    },
                    ensure_ascii=False,
                ),
            ),
        ]

    def _batch_messages(self, source_items: list[dict]) -> list[LLMMessage]:
        domain = str(source_items[0]["domain"])
        allowed_tags = ", ".join(sorted(_allowed_tags(domain)))
        entity_aliases = _entity_alias_prompt()
        items = [
            {
                "source_id": item.get("external_id"),
                "source_platform": item.get("source_platform"),
                "source_type": item.get("source_type"),
                "source_role": item.get("source_role") or "primary",
                "author_name": item.get("author_name"),
                "source_date": str(item.get("source_date")),
                "raw_title": item.get("title"),
                "raw_content": item.get("raw_content") or item.get("summary") or item.get("title"),
                "assets_count": len(item.get("assets") or []),
                "quoted_url": item.get("quoted_url"),
                "reposted_url": item.get("reposted_url"),
                "reply_to_url": item.get("reply_to_url"),
            }
            for item in source_items
        ]
        return [
            LLMMessage(
                role="system",
                content=(
                    "You cluster cleaned RSS/social sources into deduplicated intelligence events. "
                    "Merge items only when they describe the same concrete event. "
                    "Primary sources define event facts; related_discussion sources provide commentary, reactions, or amplification. "
                    "When primary sources are present, do not let discussion-only sources overwrite the factual event title. "
                    "For X/social items with duplicated title/body, write a readable event title while preserving meaning. "
                    "Return only valid JSON object. Do not include markdown. The JSON must match this shape: "
                    '{"events":[{"source_ids":["..."],"title_en":"...","title_zh":"...",'
                    '"summary_en":"...","summary_zh":"...","event_tag":"...",'
                    '"entity_ids":["..."],"importance_score":80}]}. '
                    f"Each event must choose exactly one event_tag from: {allowed_tags}. "
                    f"Infer entity_ids from the raw content using this canonical alias map: {entity_aliases}. "
                    "Entity ids must be primary subjects of the event. Do not tag an entity that is only cited as "
                    "background, related work, an example, a benchmark comparison, or inside a parenthetical list. "
                    "For paper_research, leave entity_ids empty unless the paper is specifically about that entity's "
                    "model, product, dataset, company, or system."
                ),
            ),
            LLMMessage(
                role="user",
                content=json.dumps(
                    {
                        "domain": domain,
                        "items": items,
                        "output_schema": {
                            "events": [
                                {
                                    "source_ids": ["ids from input items that belong to this event"],
                                    "title_en": "short readable English event title; use raw English post if it is already short",
                                    "title_zh": "short Chinese event title",
                                    "summary_en": "1-2 sentence English event summary or concise original content",
                                    "summary_zh": "1-2 sentence Chinese event summary",
                                    "event_tag": "one allowed tag",
                                    "entity_ids": ["canonical entity ids inferred from the grouped sources"],
                                    "importance_score": "integer 0-100",
                                }
                            ]
                        },
                    },
                    ensure_ascii=False,
                ),
            ),
        ]

    def _merge_messages(self, candidate_event: dict, existing_events: list[IntelligenceEventRow]) -> list[LLMMessage]:
        existing_payload = [
            {
                "event_key": event.event_key,
                "title_en": event.title,
                "title_zh": event.title_zh,
                "summary_en": event.summary,
                "summary_zh": event.tldr_zh,
                "event_tags": event.event_tags,
                "entity_ids": event.entity_ids,
                "last_seen_at": str(event.last_seen_at),
            }
            for event in existing_events
        ]
        candidate_payload = {
            "title_en": candidate_event.get("title"),
            "title_zh": candidate_event.get("title_zh"),
            "summary_en": candidate_event.get("summary"),
            "summary_zh": candidate_event.get("tldr_zh"),
            "event_tags": candidate_event.get("event_tags"),
            "entity_ids": candidate_event.get("entity_ids"),
            "last_seen_at": str(candidate_event.get("last_seen_at")),
        }
        return [
            LLMMessage(
                role="system",
                content=(
                    "You decide whether a new candidate intelligence event is the same concrete event as one recent existing event. "
                    "Merge only when they describe the same specific release, update, news item, paper, market move, or opinion thread. "
                    "Do not merge merely because they share the same company/entity or broad topic. "
                    "Return only valid JSON object with this shape: "
                    '{"decision":"merge","target_event_key":"...","reason":"..."} '
                    'or {"decision":"new","target_event_key":null,"reason":"..."}.'
                ),
            ),
            LLMMessage(
                role="user",
                content=json.dumps(
                    {
                        "candidate_event": candidate_payload,
                        "existing_events": existing_payload,
                    },
                    ensure_ascii=False,
                ),
            ),
        ]

    @staticmethod
    def _fallback(source_item: dict) -> SyntheticEvent:
        return SyntheticEvent(
            title=str(source_item.get("title") or "").strip(),
            title_zh=str(source_item.get("title_zh") or "").strip(),
            summary=str(source_item.get("summary") or source_item.get("raw_content") or source_item.get("title") or "").strip(),
            summary_zh=str(source_item.get("summary_zh") or source_item.get("tldr_zh") or "").strip(),
            event_tag=str((source_item.get("event_tags") or ["industry"])[0]),
            entity_ids=list(source_item.get("entity_ids") or []),
            importance_score=int(source_item.get("importance_score") or 0),
        )


def _allowed_tags(domain: str) -> set[str]:
    if domain == "finance":
        return FINANCE_EVENT_TAGS
    return AI_EVENT_TAGS


def _parse_json_object(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("LLM response must be a JSON object")
    return payload


def _normalize_entity_ids(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    seen: set[str] = set()
    result: list[str] = []
    for item in value:
        entity_id = str(item).strip().lower()
        if entity_id in ENTITY_DISPLAY and entity_id not in seen:
            seen.add(entity_id)
            result.append(entity_id)
    return result


def _filter_entity_ids_by_evidence(entity_ids: list[str], source_items: list[dict], event_tag: str) -> list[str]:
    result: list[str] = []
    for entity_id in entity_ids:
        aliases = ENTITY_ALIASES.get(entity_id, ())
        if not aliases:
            continue
        title_text = " ".join(str(item.get("title") or "") for item in source_items)
        body_text = " ".join(
            str(item.get("raw_content") or item.get("summary") or item.get("title") or "")
            for item in source_items
        )
        title_matches = _count_alias_matches(title_text, aliases)
        body_matches = _count_alias_matches(body_text, aliases)
        if title_matches > 0:
            result.append(entity_id)
            continue
        if event_tag == "paper_research" and all(str(item.get("source_platform")) == "Paper" for item in source_items):
            if body_matches >= 2:
                result.append(entity_id)
            continue
        if body_matches > 0:
            result.append(entity_id)
    return result


def _count_alias_matches(text: str, aliases: tuple[str, ...]) -> int:
    lowered = text.lower()
    count = 0
    for alias in aliases:
        normalized_alias = alias.lower()
        if re.search(rf"(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])", lowered):
            count += len(re.findall(rf"(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])", lowered))
    return count


def _first_text(payload: dict, *keys: str) -> str:
    for key in keys:
        value = str(payload.get(key) or "").strip()
        if value:
            return value
    return ""


def _parse_llm_score(value: object) -> int | None:
    try:
        score = int(value)
    except (TypeError, ValueError):
        return None
    return max(0, min(100, score))


def _entity_alias_prompt() -> dict[str, list[str]]:
    return {entity_id: list(aliases) for entity_id, aliases in ENTITY_ALIASES.items() if entity_id in ENTITY_DISPLAY}
