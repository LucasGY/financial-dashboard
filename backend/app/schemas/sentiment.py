from __future__ import annotations

from datetime import date
from typing import Optional

from app.schemas.common import APIModel, BreadthSnapshot, TimeSeriesPoint


class FearGreedSnapshot(APIModel):
    as_of_date: Optional[date]
    value: Optional[int]
    label: Optional[str]
    color: Optional[str]
    day_change: Optional[int]


class ValueSnapshot(APIModel):
    as_of_date: Optional[date]
    value: Optional[float]


class BreadthOverview(APIModel):
    spx: Optional[BreadthSnapshot]
    ndx: Optional[BreadthSnapshot]


class SentimentOverviewResponse(APIModel):
    fear_greed: FearGreedSnapshot
    vix: ValueSnapshot
    vol_structure: ValueSnapshot
    breadth: BreadthOverview


class FearGreedTrendResponse(APIModel):
    range: str
    as_of_date: Optional[date]
    start_value: Optional[int]
    end_value: Optional[int]
    min_value: Optional[int]
    max_value: Optional[int]
    series: list[TimeSeriesPoint]


class VolatilityTrendResponse(APIModel):
    range: str
    as_of_date: Optional[date]
    vix_current: Optional[float]
    vol_structure_current: Optional[float]
    vix_series: list[TimeSeriesPoint]
    vol_structure_series: list[TimeSeriesPoint]
