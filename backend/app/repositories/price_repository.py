from __future__ import annotations

from datetime import date

from app.repositories.base import BaseRepository
from app.repositories.models import PriceRow


class PriceRepository(BaseRepository):
    def fetch_series(self, tickers: list[str], start_date: date, end_date: date) -> list[PriceRow]:
        placeholders = ", ".join(["%s"] * len(tickers))
        rows = self._fetch_all(
            f"""
            SELECT i.ticker, p.trade_date, p.adj_close_price
            FROM raw_equity_daily_price p
            INNER JOIN dim_instrument i
                ON i.instrument_id = p.instrument_id
            WHERE i.ticker IN ({placeholders})
              AND p.trade_date BETWEEN %s AND %s
            ORDER BY i.ticker ASC, p.trade_date ASC
            """,
            tuple(tickers) + (start_date, end_date),
        )
        return [PriceRow(**row) for row in rows]
