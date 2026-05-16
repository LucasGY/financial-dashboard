from __future__ import annotations

from dataclasses import dataclass
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
    summary: Optional[str]
    raw_content: Optional[str]


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
    primary_source: Optional[IntelligenceSourceRow] = None
