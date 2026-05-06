from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from app.core.errors import NotFoundError
from app.core.precision import quantize_optional
from app.repositories.index_valuation_repository import IndexValuationRepository
from app.repositories.models import ValuationRow
from app.schemas.common import TimeSeriesPoint
from app.schemas.valuation import (
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


class ValuationService:
    def __init__(self, index_valuation_repository: IndexValuationRepository) -> None:
        self._index_valuation_repository = index_valuation_repository

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
