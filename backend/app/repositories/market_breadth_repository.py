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
