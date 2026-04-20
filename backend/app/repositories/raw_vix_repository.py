from app.repositories.base import BaseRepository
from app.repositories.models import VixRow


class RawVixRepository(BaseRepository):
    def fetch_latest(self, limit: int) -> list[VixRow]:
        rows = self._fetch_all(
            """
            SELECT trade_date, vix_close, vvix_close
            FROM raw_vix
            ORDER BY trade_date DESC
            LIMIT %s
            """,
            (limit,),
        )
        return [VixRow(**row) for row in rows]

    def fetch_recent(self, limit: int) -> list[VixRow]:
        rows = self._fetch_all(
            """
            SELECT trade_date, vix_close, vvix_close
            FROM (
                SELECT trade_date, vix_close, vvix_close
                FROM raw_vix
                ORDER BY trade_date DESC
                LIMIT %s
            ) recent
            ORDER BY trade_date ASC
            """,
            (limit,),
        )
        return [VixRow(**row) for row in rows]
