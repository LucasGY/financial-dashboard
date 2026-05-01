from app.repositories.base import BaseRepository
from app.repositories.models import BreadthRow


class MarketBreadthRepository(BaseRepository):
    def fetch_latest_snapshots(self) -> list[BreadthRow]:
        rows = self._fetch_all(
            """
            SELECT mb.trade_date, mb.index_name, mb.above_20d_pct, mb.above_50d_pct, mb.above_200d_pct
            FROM market_breadth mb
            INNER JOIN (
                SELECT index_name, MAX(trade_date) AS latest_trade_date
                FROM market_breadth
                GROUP BY index_name
            ) latest
                ON latest.index_name = mb.index_name
               AND latest.latest_trade_date = mb.trade_date
            """
        )
        return [BreadthRow(**row) for row in rows]

    def fetch_recent(self, index_name: str, limit: int) -> list[BreadthRow]:
        rows = self._fetch_all(
            """
            SELECT trade_date, index_name, above_20d_pct, above_50d_pct, above_200d_pct
            FROM (
                SELECT trade_date, index_name, above_20d_pct, above_50d_pct, above_200d_pct
                FROM market_breadth
                WHERE index_name = %s
                ORDER BY trade_date DESC
                LIMIT %s
            ) recent
            ORDER BY trade_date ASC
            """,
            (index_name, limit),
        )
        return [BreadthRow(**row) for row in rows]
