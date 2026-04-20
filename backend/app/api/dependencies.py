from fastapi import Depends

from app.core.config import get_settings
from app.core.database import Database
from app.repositories.index_valuation_repository import IndexValuationRepository
from app.repositories.market_breadth_repository import MarketBreadthRepository
from app.repositories.raw_fng_repository import RawFngRepository
from app.repositories.raw_vix_repository import RawVixRepository
from app.services.sentiment_service import SentimentService
from app.services.valuation_service import ValuationService


def get_database(settings=Depends(get_settings)) -> Database:
    return Database(settings)


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
