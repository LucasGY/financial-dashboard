from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class FearGreedRow:
    trade_date: date
    fng_value: Optional[int]


@dataclass(frozen=True)
class VixRow:
    trade_date: date
    vix_close: Optional[Decimal]
    vvix_close: Optional[Decimal]


@dataclass(frozen=True)
class BreadthRow:
    trade_date: date
    index_name: str
    above_20d_pct: Optional[Decimal]
    above_50d_pct: Optional[Decimal]
    above_200d_pct: Optional[Decimal]


@dataclass(frozen=True)
class ValuationRow:
    trade_date: date
    index_name: str
    pe_ntm: Optional[Decimal]


@dataclass(frozen=True)
class InstrumentRow:
    instrument_id: int
    ticker: str
    name: Optional[str]
    asset_type: str
    currency_code: str
    is_active: int


@dataclass(frozen=True)
class PriceRow:
    ticker: str
    trade_date: date
    adj_close_price: Decimal


@dataclass(frozen=True)
class IntelligenceSourceRow:
    id: int
    event_id: int
    external_id: str
    source_name: str
    source_platform: str
    source_type: str
    source_url: Optional[str]
    author_avatar_url: Optional[str]
    author_name: Optional[str]
    source_date: object
    title: str
    title_en: Optional[str] = None
    title_zh: Optional[str] = None
    summary: Optional[str] = None
    summary_en: Optional[str] = None
    summary_zh: Optional[str] = None
    raw_content: Optional[str] = None
    raw_content_en: Optional[str] = None
    raw_content_zh: Optional[str] = None
    source_role: str = "primary"
    original_url: Optional[str] = None
    quoted_url: Optional[str] = None
    reposted_url: Optional[str] = None
    reply_to_url: Optional[str] = None
    assets: list[dict] = field(default_factory=list)
    extracted_at: Optional[object] = None
    extraction_status: Optional[str] = None


@dataclass(frozen=True)
class IntelligenceEventRow:
    id: int
    event_key: str
    domain: str
    title: str
    title_zh: Optional[str]
    summary: str
    tldr_zh: Optional[str]
    first_seen_at: object
    last_seen_at: object
    entity_ids: list[str]
    event_tags: list[str]
    topic_tags: list[str]
    importance_score: int
    status: str
    source_count: int
    related_discussion_count: int = 0
    is_favorited: bool = False
    primary_source: Optional[IntelligenceSourceRow] = None
