from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


Channel = Literal["daily", "ai", "finance", "deep_dive"]
SourceKind = Literal["feed", "manual", "digest"]


class IntelligenceSource(BaseModel):
    id: str
    source_name: Optional[str] = None
    source_platform: Optional[str] = None
    source_type: Optional[str] = None
    author_name: Optional[str] = None
    author_avatar_url: Optional[str] = None
    source_date: str
    title: str
    summary: str = ""
    source_url: Optional[str] = None
    raw_content: str = ""


class IntelligenceItem(BaseModel):
    id: str
    slug: str
    channel: Channel
    domain: str
    source_kind: SourceKind
    source_platform: Optional[str] = None
    source_type: Optional[str] = None
    source_name: Optional[str] = None
    author_name: Optional[str] = None
    author_avatar_url: Optional[str] = None
    source_date: str
    title: str
    title_zh: str = ""
    summary: str = ""
    tldr_zh: str = ""
    tldr_en: str = ""
    raw_excerpt: str = ""
    raw_excerpt_zh: str = ""
    display_mode: str = "summary"
    entity_ids: list[str]
    entity_labels: list[str]
    event_tags: list[str]
    topic_tags: list[str]
    importance_score: Optional[int] = None
    source_count: int = 1
    source_url: Optional[str] = None
    status: str = "new"


class FeedResponse(BaseModel):
    items: list[IntelligenceItem]


class SourceDetail(IntelligenceItem):
    content: str
    sources: list[IntelligenceSource] = []
