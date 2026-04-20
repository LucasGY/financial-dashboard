from app.repositories.base import BaseRepository
from app.repositories.models import FearGreedRow


class RawFngRepository(BaseRepository):
    def fetch_latest(self, limit: int) -> list[FearGreedRow]:
        rows = self._fetch_all(
            """
            SELECT trade_date, fng_value
            FROM raw_fng
            ORDER BY trade_date DESC
            LIMIT %s
            """,
            (limit,),
        )
        return [FearGreedRow(**row) for row in rows]

    def fetch_recent(self, limit: int) -> list[FearGreedRow]:
        rows = self._fetch_all(
            """
            SELECT trade_date, fng_value
            FROM (
                SELECT trade_date, fng_value
                FROM raw_fng
                ORDER BY trade_date DESC
                LIMIT %s
            ) recent
            ORDER BY trade_date ASC
            """,
            (limit,),
        )
        return [FearGreedRow(**row) for row in rows]
