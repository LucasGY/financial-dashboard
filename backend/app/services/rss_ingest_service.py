from __future__ import annotations

import re
from html import unescape
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from app.repositories.intelligence_feed_repository import IntelligenceFeedRepository
from app.services.event_synthesis_service import EventSynthesisService
from app.services.rss_quality_filter import evaluate_rss_item
from app.services.rss_source_config import RssSource


class RssIngestService:
    def __init__(
        self,
        repository: IntelligenceFeedRepository,
        event_synthesizer: EventSynthesisService | None = None,
    ) -> None:
        self._repository = repository
        self._event_synthesizer = event_synthesizer

    def ingest_sources(
        self,
        sources: list[RssSource],
        limit_per_source: int | None = None,
    ) -> int:
        import feedparser

        normalized_items: list[dict] = []
        for source in sources:
            feed = feedparser.parse(source.url)
            entries = feed.entries[:limit_per_source] if limit_per_source is not None else feed.entries
            source_items: list[dict] = []
            for entry in entries:
                normalized = normalize_entry(source, entry)
                if not normalized["should_ingest"]:
                    continue
                source_items.append(normalized)
            existing_external_ids = _fetch_existing_source_external_ids(self._repository, source_items)
            normalized_items.extend(
                item for item in source_items if str(item["external_id"]) not in existing_external_ids
            )
        event_groups = group_sources_into_events(normalized_items, self._event_synthesizer)
        for source_group, synthetic_event in event_groups:
            event = build_event_payload(source_group[0], synthetic_event=synthetic_event, source_group=source_group)
            event = resolve_recent_event_merge(self._repository, self._event_synthesizer, event)
            for source_item in source_group:
                self._repository.upsert_event_with_source(event=event, source=source_item)
        return len(normalized_items)


def normalize_entry(source: RssSource, entry: dict) -> dict:
    title = _dedupe_repeated_text(_clean_rss_text(str(entry.get("title") or "")))
    summary = _dedupe_repeated_text(_clean_rss_text(str(entry.get("summary") or entry.get("description") or "")))
    if _normalized_compare(summary) == _normalized_compare(title):
        summary = ""
    elif _normalized_compare(summary).startswith(_normalized_compare(title) + " "):
        summary = summary[len(title):].strip()
    link = str(entry.get("link") or entry.get("id") or "").strip()
    source_type = _infer_source_type(source.platform)
    quality = evaluate_rss_item(
        domain=source.domain,
        source_platform=source.platform,
        source_type=source_type,
        title=title,
        summary=summary,
        entity_ids=[],
        event_tags=[],
        source_url=link or None,
    )
    return {
        "external_id": str(entry.get("id") or link or f"{source.name}:{title}"),
        "domain": source.domain,
        "source_name": source.name,
        "source_platform": source.platform,
        "source_type": source_type,
        "source_url": link or None,
        "author_avatar_url": _extract_author_avatar_url(source.platform, entry),
        "author_name": entry.get("author"),
        "source_date": _parse_entry_date(entry),
        "title": title,
        "summary": summary,
        "raw_content": summary or title,
        "entity_ids": [],
        "event_tags": [],
        "topic_tags": [],
        "should_ingest": quality.should_ingest,
        "quality_reason": quality.reason,
        "importance_score": None,
    }


def group_sources_into_events(source_items: list[dict], event_synthesizer=None) -> list[tuple[list[dict], object | None]]:
    if not source_items:
        return []
    groups: list[tuple[list[dict], object | None]] = []
    if event_synthesizer and hasattr(event_synthesizer, "synthesize_events"):
        by_domain: dict[str, list[dict]] = {}
        for item in source_items:
            by_domain.setdefault(str(item["domain"]), []).append(item)
        for items in by_domain.values():
            for chunk in _chunks(items, size=5):
                groups.extend(event_synthesizer.synthesize_events(chunk))
        return groups
    for item in source_items:
        synthetic_event = event_synthesizer.synthesize(item) if event_synthesizer else None
        groups.append(([item], synthetic_event))
    return groups


def build_event_payload(source_item: dict, synthetic_event=None, source_group: list[dict] | None = None) -> dict:
    title = synthetic_event.title if synthetic_event else source_item["title"]
    title_zh = synthetic_event.title_zh if synthetic_event else source_item.get("title_zh", "")
    summary = synthetic_event.summary if synthetic_event else (source_item["summary"] or source_item["title"])
    summary_zh = synthetic_event.summary_zh if synthetic_event else source_item.get("summary_zh", "")
    event_tags = [synthetic_event.event_tag] if synthetic_event else source_item["event_tags"]
    importance_score = synthetic_event.importance_score if synthetic_event else None
    sources = source_group or [source_item]
    first_seen_at = min(source["source_date"] for source in sources)
    last_seen_at = max(source["source_date"] for source in sources)
    entity_ids = synthetic_event.entity_ids if synthetic_event else _dedupe_entity_ids(entity_id for source in sources for entity_id in source["entity_ids"])
    topic_tags = _dedupe_entity_ids(tag for source in sources for tag in source["topic_tags"])
    return {
        "event_key": build_event_key(
            domain=source_item["domain"],
            entity_ids=entity_ids,
            event_tags=event_tags,
            title=title,
        ),
        "domain": source_item["domain"],
        "title": title,
        "title_zh": title_zh,
        "summary": summary,
        "tldr_zh": summary_zh,
        "first_seen_at": first_seen_at,
        "last_seen_at": last_seen_at,
        "entity_ids": entity_ids,
        "event_tags": event_tags,
        "topic_tags": topic_tags,
        "importance_score": importance_score,
        "status": "new",
    }


def resolve_recent_event_merge(repository, event_synthesizer, event: dict, window_hours: int = 48) -> dict:
    if not event_synthesizer or not hasattr(event_synthesizer, "match_existing_event"):
        return event
    if not hasattr(repository, "fetch_recent_merge_candidates"):
        return event
    event_tags = event.get("event_tags") or []
    if not event_tags:
        return event
    last_seen_at = event.get("last_seen_at")
    if not isinstance(last_seen_at, datetime):
        return event
    candidates = repository.fetch_recent_merge_candidates(
        domain=str(event["domain"]),
        event_tag=str(event_tags[0]),
        entity_ids=list(event.get("entity_ids") or []),
        since=last_seen_at - timedelta(hours=window_hours),
    )
    candidates = [candidate for candidate in candidates if candidate.event_key != event["event_key"]]
    target_event_key = event_synthesizer.match_existing_event(event, candidates)
    if not target_event_key:
        return event
    return {**event, "event_key": target_event_key}


def _fetch_existing_source_external_ids(repository, source_items: list[dict]) -> set[str]:
    external_ids = [str(item["external_id"]) for item in source_items]
    if not external_ids or not hasattr(repository, "fetch_existing_source_external_ids"):
        return set()
    return set(repository.fetch_existing_source_external_ids(external_ids))


def build_event_key(domain: str, entity_ids: list[str], event_tags: list[str], title: str) -> str:
    entity_part = "+".join(sorted(entity_ids)) or "unknown"
    event_part = "+".join(sorted(event_tags)) or "general"
    words = [word for word in re.findall(r"[a-z0-9]+", title.lower()) if word not in _STOP_WORDS]
    signature = "-".join(words[:4])
    return f"{domain}:{entity_part}:{event_part}:{signature}"


def _parse_entry_date(entry: dict) -> datetime:
    published = entry.get("published") or entry.get("updated")
    if published:
        parsed = parsedate_to_datetime(str(published))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return datetime.utcnow()


def _clean_rss_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _dedupe_repeated_text(value: str) -> str:
    midpoint = len(value) // 2
    if len(value) >= 12 and len(value) % 2 == 0 and value[:midpoint].strip() == value[midpoint:].strip():
        return value[:midpoint].strip()
    words = value.split()
    if len(words) >= 4 and len(words) % 2 == 0:
        half = len(words) // 2
        if words[:half] == words[half:]:
            return " ".join(words[:half])
    return value


def _normalized_compare(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _dedupe_entity_ids(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _infer_source_type(source_platform: str) -> str:
    if source_platform == "X":
        return "KOL"
    if source_platform == "Paper":
        return "Researcher"
    return source_platform


def _extract_author_avatar_url(source_platform: str, entry: dict) -> str | None:
    if source_platform != "X":
        return None
    handle = _extract_x_handle(entry)
    return f"https://unavatar.io/x/{handle}" if handle else None


def _extract_x_handle(entry: dict) -> str | None:
    link = str(entry.get("link") or entry.get("id") or "")
    match = re.search(r"(?:x|twitter)\.com/([^/?#]+)/status/", link)
    if match:
        return match.group(1)
    author = str(entry.get("author") or "").strip().lstrip("@")
    return author or None


def _chunks(items: list[dict], size: int):
    for index in range(0, len(items), size):
        yield items[index : index + size]


_STOP_WORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "in",
    "new",
    "of",
    "on",
    "the",
    "to",
    "tool",
    "tools",
    "update",
    "updates",
}
