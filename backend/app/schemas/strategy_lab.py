from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import Field, field_validator, model_validator

from app.schemas.common import APIModel, TimeSeriesPoint


SUPPORTED_TICKERS = ("SPY", "QQQ", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA")


class StrategyCondition(APIModel):
    indicator: str
    operator: str
    threshold: Optional[float] = None
    upper_threshold: Optional[float] = None
    consecutive_days: int = 1
    index_code: Optional[str] = None
    breadth_period: Optional[int] = None
    percentile_window: Optional[str] = None
    description: str


class StrategySpec(APIModel):
    prompt: str
    target_ticker: str
    logic_operator: Literal["all", "any"] = "all"
    holding_period_days: int
    forward_windows: list[int]
    entry_conditions: list[StrategyCondition]
    execution_mode: Literal["rules", "sandbox"] = "rules"
    parse_notes: list[str] = Field(default_factory=list)
    unsupported_fragments: list[str] = Field(default_factory=list)


class StrategyLabRunRequest(APIModel):
    prompt: str = Field(min_length=8, max_length=800)
    target_ticker: str
    start_date: date
    end_date: date
    forward_windows: list[int]

    @field_validator("target_ticker")
    @classmethod
    def validate_ticker(cls, value: str) -> str:
        ticker = value.upper()
        if ticker not in SUPPORTED_TICKERS:
            raise ValueError(f"target_ticker must be one of: {', '.join(SUPPORTED_TICKERS)}")
        return ticker

    @field_validator("forward_windows")
    @classmethod
    def validate_windows(cls, value: list[int]) -> list[int]:
        if not value:
            raise ValueError("forward_windows must contain at least one window")
        cleaned = sorted(set(value))
        if any(item <= 0 for item in cleaned):
            raise ValueError("forward_windows must be positive integers")
        if any(item > 252 for item in cleaned):
            raise ValueError("forward_windows must be <= 252")
        return cleaned

    @model_validator(mode="after")
    def validate_dates(self) -> "StrategyLabRunRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class StrategyRunResponse(APIModel):
    run_id: str
    status: Literal["queued", "running", "succeeded", "failed"]
    message: Optional[str] = None


class SummaryMetric(APIModel):
    window_days: int
    signal_count: int
    win_rate: Optional[float]
    avg_return: Optional[float]
    median_return: Optional[float]
    max_return: Optional[float]
    min_return: Optional[float]


class SignalEvent(APIModel):
    signal_date: date
    entry_date: Optional[date]
    forward_returns: dict[str, Optional[float]]
    met_conditions: list[str]


class ChartBarPoint(APIModel):
    label: str
    value: Optional[float]


class SignalMarkerPoint(APIModel):
    trade_date: date
    price: float
    label: str


class StrategyCharts(APIModel):
    win_rate_bars: list[ChartBarPoint]
    avg_return_bars: list[ChartBarPoint]
    price_series: list[TimeSeriesPoint]
    signal_points: list[SignalMarkerPoint]


class DataCoverage(APIModel):
    available_start_date: Optional[date]
    available_end_date: Optional[date]
    feature_start_date: Optional[date]
    feature_end_date: Optional[date]
    missing_features: list[str]
    truncated_signal_count: int


class StrategyLabResultResponse(APIModel):
    run_id: str
    strategy_spec: StrategySpec
    generated_code: str
    summary_metrics: list[SummaryMetric]
    signal_events: list[SignalEvent]
    charts: StrategyCharts
    data_coverage: DataCoverage
    warnings: list[str]
