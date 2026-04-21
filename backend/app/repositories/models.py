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
