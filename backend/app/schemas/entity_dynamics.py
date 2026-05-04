from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class FeedItem(BaseModel):
    slug: str
    source_date: str
    content_type: str
    frontend_category: str
    entity_tags: list[str]
    title: str
    title_zh: str
    tldr_zh: str
    tldr_en: str
    source_platform: Optional[str] = None
    source_url: Optional[str] = None


class FeedResponse(BaseModel):
    items: list[FeedItem]


class SourceDetail(FeedItem):
    content: str
