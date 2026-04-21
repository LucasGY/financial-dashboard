from __future__ import annotations

from datetime import date

from app.repositories.base import BaseRepository
from app.repositories.models import BreadthRow, FearGreedRow, ValuationRow, VixRow


class StrategyFeatureRepository(BaseRepository):
    def fetch_fng_series(self, start_date: date, end_date: date) -> list[FearGreedRow]:
        rows = self._fetch_all(
            """
            SELECT trade_date, fng_value
            FROM raw_fng
            WHERE trade_date BETWEEN %s AND %s
            ORDER BY trade_date ASC
            """,
            (start_date, end_date),
        )
        return [FearGreedRow(**row) for row in rows]

    def fetch_vix_series(self, start_date: date, end_date: date) -> list[VixRow]:
        rows = self._fetch_all(
            """
            SELECT trade_date, vix_close, vvix_close
            FROM raw_vix
            WHERE trade_date BETWEEN %s AND %s
            ORDER BY trade_date ASC
            """,
            (start_date, end_date),
        )
        return [VixRow(**row) for row in rows]

    def fetch_breadth_series(self, start_date: date, end_date: date, index_names: list[str]) -> list[BreadthRow]:
        placeholders = ", ".join(["%s"] * len(index_names))
        rows = self._fetch_all(
            f"""
            SELECT trade_date, index_name, above_20d_pct, above_50d_pct, above_200d_pct
            FROM market_breadth
            WHERE index_name IN ({placeholders})
              AND trade_date BETWEEN %s AND %s
            ORDER BY trade_date ASC, index_name ASC
            """,
            tuple(index_names) + (start_date, end_date),
        )
        return [BreadthRow(**row) for row in rows]

    def fetch_valuation_series(self, start_date: date, end_date: date, index_names: list[str]) -> list[ValuationRow]:
        placeholders = ", ".join(["%s"] * len(index_names))
        rows = self._fetch_all(
            f"""
            SELECT trade_date, index_name, pe_ntm
            FROM index_valuation
            WHERE index_name IN ({placeholders})
              AND trade_date BETWEEN %s AND %s
            ORDER BY trade_date ASC, index_name ASC
            """,
            tuple(index_names) + (start_date, end_date),
        )
        return [ValuationRow(**row) for row in rows]
