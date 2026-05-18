from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import frontmatter
from app.repositories.intelligence_feed_repository import IntelligenceFeedRepository
from app.repositories.models import IntelligenceEventRow, IntelligenceSourceRow
from app.schemas.entity_dynamics import FeedResponse, IntelligenceItem, IntelligenceSource, SourceDetail
from app.services.intelligence_taxonomy import entity_labels_for_channel, normalize_event_tags_for_domain


class EntityDynamicsService:
    _DEEP_DIVE_FILTERS = {"all", "interview", "manual_saved", "close_reading"}

    def __init__(
        self,
        second_brain_path: str,
        intelligence_feed_repository: IntelligenceFeedRepository,
    ) -> None:
        self._sources_dir = Path(second_brain_path) / "wiki" / "sources"
        self._intelligence_feed_repository = intelligence_feed_repository

    def get_feed(
        self,
        channel: str = "ai",
        filter_key: str = "all",
        search: Optional[str] = None,
        min_score: Optional[int] = None,
        entity: Optional[str] = None,
    ) -> FeedResponse:
        if channel in {"ai", "finance"}:
            rows = self._intelligence_feed_repository.fetch_events(
                domain=channel,
                event_tag=None if filter_key == "all" else filter_key,
                search=search,
                min_score=min_score,
                entity_id=entity if entity and entity != "all" else None,
            )
            return FeedResponse(items=[self._map_event_row(row, channel) for row in rows])
        if channel == "deep_dive":
            return FeedResponse(items=self._load_deep_dive(filter_key=filter_key, search=search))
        if channel == "daily":
            return FeedResponse(items=[])
        return FeedResponse(items=[])

    def get_detail(self, slug: str) -> Optional[SourceDetail]:
        if slug.startswith("event:"):
            return self._get_event_detail(slug)
        if slug.startswith("deep:"):
            return self._get_deep_dive_detail(slug.removeprefix("deep:"))
        return None

    def _get_event_detail(self, slug: str) -> Optional[SourceDetail]:
        try:
            event_id = int(slug.removeprefix("event:"))
        except ValueError:
            return None
        event = self._intelligence_feed_repository.fetch_event(event_id)
        if event is None:
            return None
        sources = self._intelligence_feed_repository.fetch_sources_for_event(event_id)
        item = self._map_event_row(_event_with_primary_source(event, sources), event.domain)
        return SourceDetail(
            **item.model_dump(),
            content="\n\n".join(source.raw_content or source.summary or source.title for source in sources),
            sources=[self._map_source_row(source) for source in sources],
        )

    def _load_deep_dive(self, filter_key: str, search: Optional[str]) -> list[IntelligenceItem]:
        if not self._sources_dir.exists():
            return []
        items: list[IntelligenceItem] = []
        for path in sorted(self._sources_dir.glob("*.md"), reverse=True):
            item = self._parse_deep_dive_item(path)
            if item is None:
                continue
            if filter_key in self._DEEP_DIVE_FILTERS and filter_key != "all" and filter_key not in item.event_tags:
                continue
            if search and search.lower() not in f"{item.title} {item.title_zh} {item.summary} {item.tldr_zh}".lower():
                continue
            items.append(item)
        return items

    def _get_deep_dive_detail(self, slug: str) -> Optional[SourceDetail]:
        target = self._sources_dir / f"{slug}.md"
        if not target.exists():
            return None
        item = self._parse_deep_dive_item(target)
        if item is None:
            return None
        post = frontmatter.load(target)
        return SourceDetail(**item.model_dump(), content=post.content, sources=[])

    def _parse_deep_dive_item(self, path: Path) -> Optional[IntelligenceItem]:
        try:
            post = frontmatter.load(path)
            meta = post.metadata
            frontend_category = str(meta.get("frontend_category") or "").strip()
            if frontend_category != "deep_dive":
                return None
            entity_ids = self._normalize_tags(meta.get("entity_ids") or meta.get("entity_tags"))
            event_tags = self._normalize_tags(meta.get("event_tags")) or ["manual_saved"]
            source_date = self._normalize_date(meta.get("source_date") or meta.get("date_ingested"))
            title = self._extract_title(post.content)
            return IntelligenceItem(
                id=f"deep:{path.stem}",
                slug=f"deep:{path.stem}",
                channel="deep_dive",
                domain="deep_dive",
                source_kind="manual",
                source_platform=str(meta.get("source_platform") or "Manual"),
                source_type=str(meta.get("source_type") or "Manual"),
                source_name=str(meta.get("source_name") or "Obsidian"),
                author_name=meta.get("author_name"),
                source_date=source_date,
                title=title,
                title_zh=str(meta.get("title_zh") or ""),
                summary=str(meta.get("summary") or meta.get("tldr_zh") or meta.get("tldr_en") or ""),
                tldr_zh=str(meta.get("tldr_zh") or ""),
                tldr_en=str(meta.get("tldr_en") or ""),
                raw_excerpt=str(meta.get("raw_excerpt") or ""),
                raw_excerpt_zh=str(meta.get("raw_excerpt_zh") or ""),
                display_mode="summary",
                entity_ids=entity_ids,
                entity_labels=entity_labels_for_channel(entity_ids, "deep_dive"),
                event_tags=event_tags,
                topic_tags=self._normalize_tags(meta.get("topic_tags")),
                importance_score=meta.get("importance_score"),
                source_count=1,
                source_url=meta.get("source_url"),
                status=str(meta.get("status") or "saved"),
            )
        except Exception:
            return None

    def _map_event_row(self, row: IntelligenceEventRow, channel: str) -> IntelligenceItem:
        primary = row.primary_source
        raw_excerpt = self._short_raw_excerpt(primary.raw_content if primary else None)
        return IntelligenceItem(
            id=f"event:{row.id}",
            slug=f"event:{row.id}",
            channel=channel,  # type: ignore[arg-type]
            domain=row.domain,
            source_kind="feed",
            source_platform=primary.source_platform if primary else None,
            source_type=primary.source_type if primary else None,
            source_role=primary.source_role if primary else "primary",
            source_name=primary.source_name if primary else None,
            author_name=primary.author_name if primary else None,
            author_avatar_url=primary.author_avatar_url if primary else None,
            source_date=self._normalize_date(row.last_seen_at),
            title=row.title,
            title_zh=row.title_zh or "",
            summary=row.summary,
            tldr_zh=row.tldr_zh or "",
            tldr_en=row.summary,
            raw_excerpt=raw_excerpt,
            raw_excerpt_zh=raw_excerpt if self._contains_cjk(raw_excerpt) else "",
            display_mode="raw" if raw_excerpt else "summary",
            assets=primary.assets if primary else [],
            entity_ids=row.entity_ids,
            entity_labels=entity_labels_for_channel(row.entity_ids, channel),
            event_tags=normalize_event_tags_for_domain(row.domain, row.event_tags),
            topic_tags=row.topic_tags,
            importance_score=row.importance_score,
            source_count=row.source_count,
            has_related_discussions=row.related_discussion_count > 0,
            source_url=primary.source_url if primary else None,
            status=row.status,
        )

    def _map_source_row(self, source: IntelligenceSourceRow) -> IntelligenceSource:
        return IntelligenceSource(
            id=f"source:{source.id}",
            source_name=source.source_name,
            source_platform=source.source_platform,
            source_type=source.source_type,
            source_role=source.source_role,
            original_url=source.original_url,
            quoted_url=source.quoted_url,
            reposted_url=source.reposted_url,
            reply_to_url=source.reply_to_url,
            assets=source.assets,
            extraction_status=source.extraction_status,
            author_name=source.author_name,
            author_avatar_url=source.author_avatar_url,
            source_date=self._normalize_date(source.source_date),
            title=source.title,
            summary=source.summary or "",
            source_url=source.source_url,
            raw_content=source.raw_content or "",
        )

    @staticmethod
    def _normalize_date(val: object) -> str:
        if isinstance(val, datetime):
            return val.strftime("%Y-%m-%d %H:%M")
        if isinstance(val, date):
            return val.strftime("%Y-%m-%d 00:00")
        return str(val).strip() if val else ""

    @staticmethod
    def _normalize_tags(val: object) -> list[str]:
        if isinstance(val, list):
            return [str(t) for t in val]
        if isinstance(val, str):
            return [val] if val else []
        return []

    @staticmethod
    def _extract_title(content: str) -> str:
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return match.group(1).strip() if match else "Untitled"

    @staticmethod
    def _short_raw_excerpt(content: Optional[str], max_chars: int = 180) -> str:
        text = re.sub(r"\s+", " ", content or "").strip()
        if not text or len(text) > max_chars:
            return ""
        return text

    @staticmethod
    def _contains_cjk(text: str) -> bool:
        return bool(re.search(r"[\u4e00-\u9fff]", text))


def _event_with_primary_source(event: IntelligenceEventRow, sources: list[IntelligenceSourceRow]) -> IntelligenceEventRow:
    if event.primary_source is not None or not sources:
        return event
    primary_source = next((source for source in sources if source.source_role == "primary"), sources[0])
    return IntelligenceEventRow(
        id=event.id,
        event_key=event.event_key,
        domain=event.domain,
        title=event.title,
        title_zh=event.title_zh,
        summary=event.summary,
        tldr_zh=event.tldr_zh,
        first_seen_at=event.first_seen_at,
        last_seen_at=event.last_seen_at,
        entity_ids=event.entity_ids,
        event_tags=event.event_tags,
        topic_tags=event.topic_tags,
        importance_score=event.importance_score,
        status=event.status,
        source_count=event.source_count,
        related_discussion_count=event.related_discussion_count,
        primary_source=primary_source,
    )
