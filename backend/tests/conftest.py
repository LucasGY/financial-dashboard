from collections.abc import Generator
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_sentiment_service, get_valuation_service
from app.main import create_app
from app.repositories.models import BreadthRow, FearGreedRow, ValuationRow, VixRow
from app.services.sentiment_service import SentimentService
from app.services.valuation_service import ValuationService


class FakeRawFngRepository:
    def fetch_latest(self, limit: int):
        return [
            FearGreedRow(trade_date=date(2026, 4, 18), fng_value=21),
            FearGreedRow(trade_date=date(2026, 4, 17), fng_value=24),
        ][:limit]

    def fetch_recent(self, limit: int):
        return [
            FearGreedRow(trade_date=date(2026, 4, 16), fng_value=31),
            FearGreedRow(trade_date=date(2026, 4, 17), fng_value=None),
            FearGreedRow(trade_date=date(2026, 4, 18), fng_value=21),
        ][:limit]


class FakeRawVixRepository:
    def fetch_latest(self, limit: int):
        return [
            VixRow(trade_date=date(2026, 4, 18), vix_close=Decimal("18.32"), vvix_close=Decimal("119.45")),
        ][:limit]

    def fetch_recent(self, limit: int):
        return [
            VixRow(trade_date=date(2026, 4, 16), vix_close=Decimal("17.85"), vvix_close=Decimal("119.00")),
            VixRow(trade_date=date(2026, 4, 17), vix_close=Decimal("0"), vvix_close=Decimal("120.00")),
            VixRow(trade_date=date(2026, 4, 18), vix_close=Decimal("18.32"), vvix_close=Decimal("119.45")),
        ][:limit]


class FakeMarketBreadthRepository:
    def fetch_latest_snapshots(self):
        return [
            BreadthRow(
                trade_date=date(2026, 4, 18),
                index_name="SP500",
                above_20d_pct=Decimal("82.12"),
                above_50d_pct=Decimal("65.00"),
                above_200d_pct=None,
            ),
            BreadthRow(
                trade_date=date(2026, 4, 18),
                index_name="NDX100",
                above_20d_pct=Decimal("15.01"),
                above_50d_pct=Decimal("45.49"),
                above_200d_pct=Decimal("60.00"),
            ),
        ]


class FakeIndexValuationRepository:
    def fetch_series(self, aliases, start_date):
        if "SPX" in aliases:
            return [
                ValuationRow(trade_date=date(2026, 1, 31), index_name="SPX", pe_ntm=Decimal("17.1234")),
                ValuationRow(trade_date=date(2026, 2, 28), index_name="SP500", pe_ntm=None),
                ValuationRow(trade_date=date(2026, 3, 31), index_name="S&P 500", pe_ntm=Decimal("18.4000")),
            ]
        if "NDX" in aliases:
            return []
        return []


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app = create_app()
    app.dependency_overrides[get_sentiment_service] = lambda: SentimentService(
        raw_fng_repository=FakeRawFngRepository(),
        raw_vix_repository=FakeRawVixRepository(),
        market_breadth_repository=FakeMarketBreadthRepository(),
    )
    app.dependency_overrides[get_valuation_service] = lambda: ValuationService(
        index_valuation_repository=FakeIndexValuationRepository(),
    )

    with TestClient(app) as test_client:
        yield test_client
