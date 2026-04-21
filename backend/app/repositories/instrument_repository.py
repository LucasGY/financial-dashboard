from app.repositories.base import BaseRepository
from app.repositories.models import InstrumentRow


class InstrumentRepository(BaseRepository):
    def fetch_active_instruments(self, tickers: list[str]) -> list[InstrumentRow]:
        placeholders = ", ".join(["%s"] * len(tickers))
        rows = self._fetch_all(
            f"""
            SELECT instrument_id, ticker, name, asset_type, currency_code, is_active
            FROM dim_instrument
            WHERE ticker IN ({placeholders})
              AND is_active = 1
            ORDER BY ticker ASC
            """,
            tuple(tickers),
        )
        return [InstrumentRow(**row) for row in rows]
