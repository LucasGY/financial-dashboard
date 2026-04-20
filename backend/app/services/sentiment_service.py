from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.core.precision import quantize_optional
from app.repositories.market_breadth_repository import MarketBreadthRepository
from app.repositories.models import BreadthRow, FearGreedRow, VixRow
from app.repositories.raw_fng_repository import RawFngRepository
from app.repositories.raw_vix_repository import RawVixRepository
from app.schemas.common import BreadthSnapshot, TimeSeriesPoint
from app.schemas.sentiment import (
    BreadthOverview,
    FearGreedSnapshot,
    FearGreedTrendResponse,
    SentimentOverviewResponse,
    ValueSnapshot,
    VolatilityTrendResponse,
)
from app.services.mapping_service import get_display_name, map_breadth_index, map_fng_label_color


class SentimentService:
    def __init__(
        self,
        raw_fng_repository: RawFngRepository,
        raw_vix_repository: RawVixRepository,
        market_breadth_repository: MarketBreadthRepository,
    ) -> None:
        self._raw_fng_repository = raw_fng_repository
        self._raw_vix_repository = raw_vix_repository
        self._market_breadth_repository = market_breadth_repository

    def get_overview(self) -> SentimentOverviewResponse:
        fng_rows = self._raw_fng_repository.fetch_latest(limit=2)
        vix_rows = self._raw_vix_repository.fetch_latest(limit=1)
        breadth_rows = self._market_breadth_repository.fetch_latest_snapshots()

        fear_greed = self._build_fear_greed_snapshot(fng_rows)
        vix_snapshot = self._build_vix_snapshot(vix_rows[0] if vix_rows else None)
        vol_snapshot = self._build_vol_structure_snapshot(vix_rows[0] if vix_rows else None)
        breadth = self._build_breadth_overview(breadth_rows)

        return SentimentOverviewResponse(
            fear_greed=fear_greed,
            vix=vix_snapshot,
            vol_structure=vol_snapshot,
            breadth=breadth,
        )

    def get_fear_greed_trend(self, range_value: str) -> FearGreedTrendResponse:
        limit = self._resolve_range(range_value)
        rows = self._raw_fng_repository.fetch_recent(limit=limit)
        series = [TimeSeriesPoint(trade_date=row.trade_date, value=row.fng_value) for row in rows]
        values = [row.fng_value for row in rows if row.fng_value is not None]

        return FearGreedTrendResponse(
            range=range_value,
            as_of_date=rows[-1].trade_date if rows else None,
            start_value=rows[0].fng_value if rows else None,
            end_value=rows[-1].fng_value if rows else None,
            min_value=min(values) if values else None,
            max_value=max(values) if values else None,
            series=series,
        )

    def get_volatility_trend(self, range_value: str) -> VolatilityTrendResponse:
        limit = self._resolve_range(range_value)
        rows = self._raw_vix_repository.fetch_recent(limit=limit)
        vix_series = [
            TimeSeriesPoint(trade_date=row.trade_date, value=quantize_optional(row.vix_close, 2))
            for row in rows
        ]
        vol_structure_series = [
            TimeSeriesPoint(
                trade_date=row.trade_date,
                value=quantize_optional(self._compute_vol_structure(row.vvix_close, row.vix_close), 4),
            )
            for row in rows
        ]
        latest_row = rows[-1] if rows else None

        return VolatilityTrendResponse(
            range=range_value,
            as_of_date=latest_row.trade_date if latest_row else None,
            vix_current=quantize_optional(latest_row.vix_close, 2) if latest_row else None,
            vol_structure_current=quantize_optional(
                self._compute_vol_structure(
                    latest_row.vvix_close if latest_row else None,
                    latest_row.vix_close if latest_row else None,
                ),
                4,
            )
            if latest_row
            else None,
            vix_series=vix_series,
            vol_structure_series=vol_structure_series,
        )

    def get_breadth(self) -> BreadthOverview:
        rows = self._market_breadth_repository.fetch_latest_snapshots()
        return self._build_breadth_overview(rows)

    @staticmethod
    def _resolve_range(range_value: str) -> int:
        return 30 if range_value == "30d" else 30

    @staticmethod
    def _compute_vol_structure(vvix_close: Optional[Decimal], vix_close: Optional[Decimal]) -> Optional[Decimal]:
        if vvix_close is None or vix_close in (None, Decimal("0")):
            return None
        return vvix_close / vix_close / Decimal("3.5")

    def _build_fear_greed_snapshot(self, rows: list[FearGreedRow]) -> FearGreedSnapshot:
        latest = rows[0] if rows else None
        previous = rows[1] if len(rows) > 1 else None
        label, color = map_fng_label_color(latest.fng_value if latest else None)
        day_change = None
        if latest and previous and latest.fng_value is not None and previous.fng_value is not None:
            day_change = latest.fng_value - previous.fng_value

        return FearGreedSnapshot(
            as_of_date=latest.trade_date if latest else None,
            value=latest.fng_value if latest else None,
            label=label,
            color=color,
            day_change=day_change,
        )

    @staticmethod
    def _build_vix_snapshot(row: Optional[VixRow]) -> ValueSnapshot:
        return ValueSnapshot(
            as_of_date=row.trade_date if row else None,
            value=quantize_optional(row.vix_close, 2) if row else None,
        )

    def _build_vol_structure_snapshot(self, row: Optional[VixRow]) -> ValueSnapshot:
        return ValueSnapshot(
            as_of_date=row.trade_date if row else None,
            value=quantize_optional(
                self._compute_vol_structure(row.vvix_close, row.vix_close) if row else None,
                4,
            )
            if row
            else None,
        )

    def _build_breadth_overview(self, rows: list[BreadthRow]) -> BreadthOverview:
        snapshots: dict[str, BreadthSnapshot] = {}
        for row in rows:
            index_code = map_breadth_index(row.index_name)
            if index_code is None:
                continue
            snapshots[index_code.lower()] = BreadthSnapshot(
                index_code=index_code,
                display_name=get_display_name(index_code),
                as_of_date=row.trade_date,
                above_20d_pct=quantize_optional(row.above_20d_pct, 2),
                above_50d_pct=quantize_optional(row.above_50d_pct, 2),
                above_200d_pct=quantize_optional(row.above_200d_pct, 2),
            )

        return BreadthOverview(spx=snapshots.get("spx"), ndx=snapshots.get("ndx"))
