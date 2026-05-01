from typing import Literal

from fastapi import APIRouter, Depends

from app.api.dependencies import get_market_regime_service
from app.schemas.market_regime import MarketRegimeOverviewResponse, MarketRegimeStatsResponse
from app.services.market_regime_service import MarketRegimeService

router = APIRouter()


@router.get("/overview", response_model=MarketRegimeOverviewResponse)
def get_overview(
    window: Literal["1y", "5y", "10y"] = "1y",
    service: MarketRegimeService = Depends(get_market_regime_service),
) -> MarketRegimeOverviewResponse:
    return service.get_overview(window)


@router.get("/stats", response_model=MarketRegimeStatsResponse)
def get_stats(
    ticker: Literal["SPY", "QQQ"],
    window: Literal["1y", "5y", "10y"] = "1y",
    service: MarketRegimeService = Depends(get_market_regime_service),
) -> MarketRegimeStatsResponse:
    return service.get_stats(ticker, window)
