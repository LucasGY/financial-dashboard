from __future__ import annotations

from datetime import date
from typing import Optional

from app.schemas.common import APIModel, TimeSeriesPoint


class ValuationTimelineResponse(APIModel):
    index_code: str
    display_name: str
    window: str
    as_of_date: Optional[date]
    estimated_date: Optional[date]
    estimate_method: str
    valuation_source: str
    is_estimated: bool
    raw_pe_ntm: Optional[float]
    based_on_trade_date: Optional[date]
    proxy_ticker: Optional[str]
    proxy_return: Optional[float]
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


class PriceAttributionPoint(APIModel):
    label: str
    start_date: date
    end_date: date
    price_start: Optional[float]
    price_end: Optional[float]
    eps_start: Optional[float]
    eps_end: Optional[float]
    pe_start: Optional[float]
    pe_end: Optional[float]
    total_return: Optional[float]
    eps_contribution: Optional[float]
    valuation_contribution: Optional[float]


class PriceAttributionResponse(APIModel):
    index_code: str
    display_name: str
    ticker: str
    tag: str
    as_of_date: Optional[date]
    series: list[PriceAttributionPoint]


class DrawdownScenarioPoint(APIModel):
    drawdown_pct: float
    price_level: Optional[float]
    implied_pe: Optional[float]
    percentile_1y: Optional[float]
    percentile_5y: Optional[float]
    percentile_10y: Optional[float]
    is_current_drawdown_row: bool
    is_key_drawdown: bool
    is_cheap: bool


class DrawdownScenarioTable(APIModel):
    ticker: str
    index_code: str
    display_name: str
    as_of_date: Optional[date]
    current_price: Optional[float]
    high_price: Optional[float]
    current_drawdown_pct: Optional[float]
    current_pe: Optional[float]
    scenarios: list[DrawdownScenarioPoint]


class DrawdownScenariosResponse(APIModel):
    spy: Optional[DrawdownScenarioTable]
    qqq: Optional[DrawdownScenarioTable]
