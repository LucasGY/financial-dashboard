from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import frontmatter

from app.schemas.entity_dynamics import FeedItem, FeedResponse, SourceDetail


class EntityDynamicsService:
    _MAG7_TAGS = {"AMZN", "MSFT", "NVDA", "AAPL", "META", "GOOGL", "TSLA", "BRK", "TSMC"}
    _AI_TAGS = {"OpenAI", "Anthropic"}
    _CONTENT_PLATFORMS = {"YouTube", "X", "WeChat", "Web"}
    _FRONTEND_CATEGORIES = {"mag7", "ai", "content"}

    def __init__(self, second_brain_path: str) -> None:
        self._sources_dir = Path(second_brain_path) / "wiki" / "sources"

    def get_feed(self) -> FeedResponse:
        return FeedResponse(items=self._load_all())

    def get_detail(self, slug: str) -> Optional[SourceDetail]:
        target = self._sources_dir / f"{slug}.md"
        if not target.exists():
            return None
        return self._parse_detail(target)

    def _load_all(self) -> list[FeedItem]:
        if not self._sources_dir.exists():
            return []
        items: list[FeedItem] = []
        for path in sorted(self._sources_dir.glob("*.md"), reverse=True):
            item = self._parse_item(path)
            if item is not None:
                items.append(item)
        return items

    def _parse_item(self, path: Path) -> Optional[FeedItem]:
        try:
            post = frontmatter.load(path)
            meta = post.metadata
            frontend_category = str(meta.get("frontend_category") or "").strip()
            entity_tags = self._normalize_tags(meta.get("entity_tags"))
            source_path = str(meta.get("source_path") or "")
            source_platform = str(meta.get("source_platform") or "").strip()
            if not self._is_frontend_eligible(frontend_category, entity_tags, source_path, source_platform):
                return None
            entity_tags = self._filter_entity_tags(frontend_category, entity_tags)
            return FeedItem(
                slug=path.stem,
                source_date=self._normalize_date(meta.get("source_date") or meta.get("date_ingested")),
                content_type=str(meta.get("content_type", "article")),
                frontend_category=frontend_category,
                entity_tags=entity_tags,
                title=self._extract_title(post.content),
                title_zh=str(meta.get("title_zh") or ""),
                tldr_zh=str(meta.get("tldr_zh") or ""),
                tldr_en=str(meta.get("tldr_en") or ""),
                source_platform=source_platform or None,
                source_url=meta.get("source_url") or None,
            )
        except Exception:
            return None

    def _parse_detail(self, path: Path) -> Optional[SourceDetail]:
        try:
            post = frontmatter.load(path)
            meta = post.metadata
            frontend_category = str(meta.get("frontend_category") or "").strip()
            entity_tags = self._normalize_tags(meta.get("entity_tags"))
            source_path = str(meta.get("source_path") or "")
            source_platform = str(meta.get("source_platform") or "").strip()
            if not self._is_frontend_eligible(frontend_category, entity_tags, source_path, source_platform):
                return None
            entity_tags = self._filter_entity_tags(frontend_category, entity_tags)
            return SourceDetail(
                slug=path.stem,
                source_date=self._normalize_date(meta.get("source_date") or meta.get("date_ingested")),
                content_type=str(meta.get("content_type", "article")),
                frontend_category=frontend_category,
                entity_tags=entity_tags,
                title=self._extract_title(post.content),
                title_zh=str(meta.get("title_zh") or ""),
                tldr_zh=str(meta.get("tldr_zh") or ""),
                tldr_en=str(meta.get("tldr_en") or ""),
                source_platform=source_platform or None,
                source_url=meta.get("source_url") or None,
                content=post.content,
            )
        except Exception:
            return None

    @classmethod
    def _is_frontend_eligible(
        cls, frontend_category: str, entity_tags: list[str], source_path: str, source_platform: str
    ) -> bool:
        if frontend_category not in cls._FRONTEND_CATEGORIES:
            return False
        if frontend_category == "mag7":
            return any(tag in cls._MAG7_TAGS for tag in entity_tags)
        if frontend_category == "ai":
            return any(tag in cls._AI_TAGS for tag in entity_tags)
        return source_path.startswith("raw/manual/") and source_platform in cls._CONTENT_PLATFORMS

    @classmethod
    def _filter_entity_tags(cls, frontend_category: str, entity_tags: list[str]) -> list[str]:
        if frontend_category == "mag7":
            return [tag for tag in entity_tags if tag in cls._MAG7_TAGS]
        if frontend_category == "ai":
            return [tag for tag in entity_tags if tag in cls._AI_TAGS]
        return entity_tags

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
