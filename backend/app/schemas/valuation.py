from __future__ import annotations

from datetime import date
from typing import Optional

from app.schemas.common import APIModel, TimeSeriesPoint


class ValuationTimelineResponse(APIModel):
    index_code: str
    display_name: str
    window: str
    as_of_date: Optional[date]
    current_value: Optional[float]
    percentile: Optional[float]
    series: list[TimeSeriesPoint]


class ValuationOverviewItem(APIModel):
    index_code: str
    display_name: str
    as_of_date: Optional[date]
    current_value: Optional[float]
    percentile_1y: Optional[float]
    percentile_5y: Optional[float]
    percentile_10y: Optional[float]


class ValuationOverviewResponse(APIModel):
    spx: Optional[ValuationOverviewItem]
    ndx: Optional[ValuationOverviewItem]
