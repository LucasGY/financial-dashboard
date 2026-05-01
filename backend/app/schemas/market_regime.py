from __future__ import annotations

from datetime import date
from typing import Optional

from app.schemas.common import APIModel


class MarketRegimeCondition(APIModel):
    key: str
    label: str
    value: Optional[float]
    unit: Optional[str] = None
    bucket: Optional[int] = None
    percentile: Optional[float] = None
    bucket_label: str


class MarketRegimeMetric(APIModel):
    window_days: int
    signal_count: int
    win_rate: Optional[float]
    avg_return: Optional[float]
    median_return: Optional[float]
    max_return: Optional[float]
    min_return: Optional[float]


class MarketRegimeStatsResponse(APIModel):
    ticker: str
    index_code: str
    window: str
    as_of_date: Optional[date]
    entry_price: Optional[float]
    conditions: list[MarketRegimeCondition]
    metrics: list[MarketRegimeMetric]
    warnings: list[str]


class MarketRegimeOverviewResponse(APIModel):
    window: str
    items: list[MarketRegimeStatsResponse]
