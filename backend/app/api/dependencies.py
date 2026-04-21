from functools import lru_cache

from fastapi import Depends

from app.core.config import get_settings
from app.core.database import Database
from app.repositories.index_valuation_repository import IndexValuationRepository
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.market_breadth_repository import MarketBreadthRepository
from app.repositories.price_repository import PriceRepository
from app.repositories.raw_fng_repository import RawFngRepository
from app.repositories.raw_vix_repository import RawVixRepository
from app.repositories.strategy_feature_repository import StrategyFeatureRepository
from app.services.backtest_service import BacktestService
from app.services.llm.providers.openai_compatible import OpenAICompatibleProvider
from app.services.sandbox_service import SandboxService
from app.services.sentiment_service import SentimentService
from app.services.strategy_codegen_service import StrategyCodegenService
from app.services.strategy_lab_service import StrategyLabService
from app.services.strategy_parser_service import StrategyParserService
from app.services.strategy_run_store import StrategyRunStore
from app.services.valuation_service import ValuationService


def get_database(settings=Depends(get_settings)) -> Database:
    return Database(settings)


@lru_cache(maxsize=1)
def get_strategy_run_store() -> StrategyRunStore:
    return StrategyRunStore()


def get_sentiment_service(database: Database = Depends(get_database)) -> SentimentService:
    return SentimentService(
        raw_fng_repository=RawFngRepository(database),
        raw_vix_repository=RawVixRepository(database),
        market_breadth_repository=MarketBreadthRepository(database),
    )


def get_valuation_service(database: Database = Depends(get_database)) -> ValuationService:
    return ValuationService(
        index_valuation_repository=IndexValuationRepository(database),
    )


def get_strategy_lab_service(database: Database = Depends(get_database)) -> StrategyLabService:
    settings = get_settings()
    llm_provider = OpenAICompatibleProvider(settings)
    return StrategyLabService(
        parser_service=StrategyParserService(llm_provider=llm_provider),
        codegen_service=StrategyCodegenService(),
        backtest_service=BacktestService(
            price_repository=PriceRepository(database),
            strategy_feature_repository=StrategyFeatureRepository(database),
            sandbox_service=SandboxService(),
        ),
        run_store=get_strategy_run_store(),
    )
