from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from math import log
from typing import Optional

from app.core.errors import NotFoundError
from app.core.precision import quantize_optional
from app.repositories.index_valuation_repository import IndexValuationRepository
from app.repositories.models import PriceRow, ValuationRow
from app.repositories.price_repository import PriceRepository
from app.schemas.common import TimeSeriesPoint
from app.schemas.valuation import (
    PriceAttributionPoint,
    PriceAttributionResponse,
    ValuationOverviewItem,
    ValuationOverviewResponse,
    ValuationTimelineResponse,
)
from app.services.mapping_service import get_display_name, get_index_aliases


WINDOW_DAYS = {
    "1y": 365,
    "5y": 365 * 5,
    "10y": 365 * 10,
}

INDEX_PRICE_TICKERS = {
    "SPX": "SPY",
    "NDX": "QQQ",
}


class ValuationService:
    def __init__(self, index_valuation_repository: IndexValuationRepository, price_repository: PriceRepository) -> None:
        self._index_valuation_repository = index_valuation_repository
        self._price_repository = price_repository

    def get_timeline(self, index_code: str, window: str) -> ValuationTimelineResponse:
        rows = self._fetch_rows(index_code=index_code, window=window)
        if not rows:
            raise NotFoundError(f"no valuation data found for index={index_code} within window={window}")

        current = rows[-1]
        values = [row.pe_ntm for row in rows if row.pe_ntm is not None]

        return ValuationTimelineResponse(
            index_code=index_code,
            display_name=get_display_name(index_code),
            window=window,
            as_of_date=current.trade_date,
            estimated_date=current.trade_date if current.is_estimated else None,
            estimate_method=current.valuation_source,
            valuation_source=current.valuation_source,
            is_estimated=bool(current.is_estimated),
            raw_pe_ntm=quantize_optional(current.raw_pe_ntm, 4),
            based_on_trade_date=current.based_on_trade_date,
            proxy_ticker=current.proxy_ticker,
            proxy_return=self._round_proxy_return(current.proxy_return),
            current_value=quantize_optional(current.pe_ntm, 4),
            percentile=self._compute_percentile(current.pe_ntm, values),
            series=[
                TimeSeriesPoint(trade_date=row.trade_date, value=quantize_optional(row.pe_ntm, 4))
                for row in rows
            ],
        )

    def get_overview(self) -> ValuationOverviewResponse:
        return ValuationOverviewResponse(
            spx=self._build_overview_item("SPX"),
            ndx=self._build_overview_item("NDX"),
        )

    def get_price_attribution(self, index_code: str, tag: str) -> PriceAttributionResponse:
        ticker = INDEX_PRICE_TICKERS[index_code]
        start_date = date.today() - timedelta(days=365)
        end_date = date.today()
        aliases = get_index_aliases(index_code)
        valuation_rows = self._index_valuation_repository.fetch_series(aliases=aliases, start_date=start_date)
        price_rows = self._price_repository.fetch_series(tickers=[ticker], start_date=start_date, end_date=end_date)
        points = self._build_attribution_points(
            tag=tag,
            valuation_rows=valuation_rows,
            price_rows=[row for row in price_rows if row.ticker == ticker],
        )

        if not points:
            raise NotFoundError(f"no price attribution data found for index={index_code} tag={tag}")

        return PriceAttributionResponse(
            index_code=index_code,
            display_name=get_display_name(index_code),
            ticker=ticker,
            tag=tag,
            as_of_date=points[-1].end_date,
            series=points,
        )

    def _build_overview_item(self, index_code: str) -> Optional[ValuationOverviewItem]:
        timeline_10y = self._fetch_rows(index_code=index_code, window="10y")
        if not timeline_10y:
            return None

        latest = timeline_10y[-1]
        item = ValuationOverviewItem(
            index_code=index_code,
            display_name=get_display_name(index_code),
            as_of_date=latest.trade_date,
            current_value=quantize_optional(latest.pe_ntm, 4),
            percentile_1y=self._timeline_percentile(index_code, "1y"),
            percentile_5y=self._timeline_percentile(index_code, "5y"),
            percentile_10y=self._timeline_percentile(index_code, "10y"),
        )
        return item

    def _timeline_percentile(self, index_code: str, window: str) -> Optional[float]:
        rows = self._fetch_rows(index_code=index_code, window=window)
        if not rows:
            return None
        current = rows[-1].pe_ntm
        values = [row.pe_ntm for row in rows if row.pe_ntm is not None]
        return self._compute_percentile(current, values)

    def _fetch_rows(self, index_code: str, window: str) -> list[ValuationRow]:
        aliases = get_index_aliases(index_code)
        cutoff = date.today() - timedelta(days=WINDOW_DAYS[window])
        return self._index_valuation_repository.fetch_series(aliases=aliases, start_date=cutoff)

    @staticmethod
    def _compute_percentile(current_value, values) -> Optional[float]:
        if current_value is None or not values:
            return None
        below_or_equal = sum(1 for value in values if value <= current_value)
        percentile = (below_or_equal / len(values)) * 100
        return round(percentile, 2)

    def _build_attribution_points(
        self,
        tag: str,
        valuation_rows: list[ValuationRow],
        price_rows: list[PriceRow],
    ) -> list[PriceAttributionPoint]:
        valuation_by_date = {
            row.trade_date: row.pe_ntm
            for row in valuation_rows
            if row.pe_ntm is not None and row.pe_ntm > 0
        }
        price_by_date = {
            row.trade_date: row.adj_close_price
            for row in price_rows
            if row.adj_close_price is not None and row.adj_close_price > 0
        }
        aligned_dates = sorted(set(valuation_by_date).intersection(price_by_date))
        periods: dict[tuple[int, int], list[date]] = {}

        for trade_date in aligned_dates:
            period_key = self._period_key(trade_date, tag)
            periods.setdefault(period_key, []).append(trade_date)

        points: list[PriceAttributionPoint] = []
        for _, period_dates in sorted(periods.items()):
            if len(period_dates) < 2:
                continue

            start = period_dates[0]
            end = period_dates[-1]
            price_start = price_by_date[start]
            price_end = price_by_date[end]
            pe_start = valuation_by_date[start]
            pe_end = valuation_by_date[end]
            eps_start = price_start / pe_start
            eps_end = price_end / pe_end

            points.append(
                PriceAttributionPoint(
                    label=self._period_label(start, end, tag),
                    start_date=start,
                    end_date=end,
                    price_start=self._round_decimal(price_start),
                    price_end=self._round_decimal(price_end),
                    eps_start=self._round_decimal(eps_start),
                    eps_end=self._round_decimal(eps_end),
                    pe_start=self._round_decimal(pe_start),
                    pe_end=self._round_decimal(pe_end),
                    total_return=self._log_change(price_start, price_end),
                    eps_contribution=self._log_change(eps_start, eps_end),
                    valuation_contribution=self._log_change(pe_start, pe_end),
                )
            )

        return points

    @staticmethod
    def _period_key(trade_date: date, tag: str) -> tuple[int, int]:
        if tag == "week":
            iso_year, iso_week, _ = trade_date.isocalendar()
            return iso_year, iso_week
        return trade_date.year, trade_date.month

    @staticmethod
    def _period_label(start: date, end: date, tag: str) -> str:
        if tag == "week":
            return f"{start.month}/{start.day}-{end.month}/{end.day}"
        return f"{end.year}-{end.month:02d}"

    @staticmethod
    def _log_change(start: Decimal, end: Decimal) -> float:
        return round(log(float(end / start)) * 100, 2)

    @staticmethod
    def _round_decimal(value: Decimal) -> float:
        return round(float(value), 4)

    @staticmethod
    def _round_proxy_return(value: Optional[Decimal]) -> Optional[float]:
        return round(float(value), 8) if value is not None else None
