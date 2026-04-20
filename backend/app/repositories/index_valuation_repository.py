from datetime import date

from app.repositories.base import BaseRepository
from app.repositories.models import ValuationRow


class IndexValuationRepository(BaseRepository):
    def fetch_series(self, aliases: list[str], start_date: date) -> list[ValuationRow]:
        placeholders = ", ".join(["%s"] * len(aliases))
        rows = self._fetch_all(
            f"""
            SELECT trade_date, index_name, pe_ntm
            FROM index_valuation
            WHERE index_name IN ({placeholders})
              AND trade_date >= %s
            ORDER BY trade_date ASC
            """,
            tuple(aliases) + (start_date,),
        )
        return [ValuationRow(**row) for row in rows]
