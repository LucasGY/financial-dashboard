from collections.abc import Generator
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_sentiment_service, get_strategy_lab_service, get_valuation_service
from app.main import create_app
from app.repositories.models import BreadthRow, FearGreedRow, PriceRow, ValuationRow, VixRow
from app.schemas.strategy_lab import StrategyLabResultResponse, StrategyLabRunRequest, StrategyRunResponse
from app.services.backtest_service import BacktestService
from app.services.sandbox_service import SandboxService
from app.services.sentiment_service import SentimentService
from app.services.strategy_codegen_service import StrategyCodegenService
from app.services.strategy_lab_service import StrategyLabService
from app.services.strategy_parser_service import StrategyParserService
from app.services.strategy_run_store import StrategyRunStore
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


class FakePriceRepository:
    def fetch_series(self, tickers, start_date, end_date):
        rows: list[PriceRow] = []
        for ticker in tickers:
            prices = {
                "SPY": [100, 101, 105, 104, 107, 108, 110, 112],
                "QQQ": [200, 201, 203, 205, 204, 206, 209, 210],
                "NVDA": [50, 52, 51, 49, 48, 50, 53, 55],
            }.get(ticker, [10, 10.5, 10.7, 11, 11.2, 11.5, 11.8, 12])
            for offset, price in enumerate(prices):
                rows.append(
                    PriceRow(
                        ticker=ticker,
                        trade_date=date(2026, 4, 1 + offset),
                        adj_close_price=Decimal(str(price)),
                    )
                )
        return rows


class FakeStrategyFeatureRepository:
    def fetch_fng_series(self, start_date, end_date):
        return [
            FearGreedRow(trade_date=date(2026, 4, 1), fng_value=16),
            FearGreedRow(trade_date=date(2026, 4, 2), fng_value=19),
            FearGreedRow(trade_date=date(2026, 4, 3), fng_value=28),
            FearGreedRow(trade_date=date(2026, 4, 4), fng_value=35),
        ]

    def fetch_vix_series(self, start_date, end_date):
        return [
            VixRow(trade_date=date(2026, 4, 1), vix_close=Decimal("24.54"), vvix_close=Decimal("114.80")),
            VixRow(trade_date=date(2026, 4, 2), vix_close=Decimal("23.87"), vvix_close=Decimal("115.30")),
            VixRow(trade_date=date(2026, 4, 3), vix_close=Decimal("26.10"), vvix_close=Decimal("120.40")),
            VixRow(trade_date=date(2026, 4, 4), vix_close=Decimal("24.00"), vvix_close=Decimal("110.00")),
        ]

    def fetch_breadth_series(self, start_date, end_date, index_names):
        return [
            BreadthRow(
                trade_date=date(2026, 4, 1),
                index_name="SP500",
                above_20d_pct=Decimal("45.12"),
                above_50d_pct=Decimal("40.00"),
                above_200d_pct=Decimal("38.00"),
            ),
            BreadthRow(
                trade_date=date(2026, 4, 2),
                index_name="SP500",
                above_20d_pct=Decimal("52.48"),
                above_50d_pct=Decimal("49.00"),
                above_200d_pct=Decimal("41.00"),
            ),
        ]

    def fetch_valuation_series(self, start_date, end_date, index_names):
        if "S&P 500 - PE - NTM" in index_names:
            return [
                ValuationRow(trade_date=date(2025, 4, 1), index_name="S&P 500 - PE - NTM", pe_ntm=Decimal("17.0")),
                ValuationRow(trade_date=date(2026, 4, 1), index_name="S&P 500 - PE - NTM", pe_ntm=Decimal("16.5")),
                ValuationRow(trade_date=date(2026, 4, 2), index_name="S&P 500 - PE - NTM", pe_ntm=Decimal("16.0")),
            ]
        return []


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app = create_app()
    strategy_lab_service = StrategyLabService(
        parser_service=StrategyParserService(),
        codegen_service=StrategyCodegenService(),
        backtest_service=BacktestService(
            price_repository=FakePriceRepository(),
            strategy_feature_repository=FakeStrategyFeatureRepository(),
            sandbox_service=SandboxService(),
        ),
        run_store=StrategyRunStore(),
    )
    app.dependency_overrides[get_sentiment_service] = lambda: SentimentService(
        raw_fng_repository=FakeRawFngRepository(),
        raw_vix_repository=FakeRawVixRepository(),
        market_breadth_repository=FakeMarketBreadthRepository(),
    )
    app.dependency_overrides[get_valuation_service] = lambda: ValuationService(
        index_valuation_repository=FakeIndexValuationRepository(),
    )
    app.dependency_overrides[get_strategy_lab_service] = lambda: strategy_lab_service

    with TestClient(app) as test_client:
        yield test_client
