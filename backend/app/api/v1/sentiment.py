from typing import Literal

from fastapi import APIRouter, Depends

from app.api.dependencies import get_sentiment_service
from app.schemas.sentiment import BreadthOverview, FearGreedTrendResponse, SentimentOverviewResponse, VolatilityTrendResponse
from app.services.sentiment_service import SentimentService

router = APIRouter()


@router.get("/overview", response_model=SentimentOverviewResponse)
def get_overview(service: SentimentService = Depends(get_sentiment_service)) -> SentimentOverviewResponse:
    return service.get_overview()


@router.get("/fear-greed/trend", response_model=FearGreedTrendResponse)
def get_fear_greed_trend(
    range: Literal["30d"] = "30d",
    service: SentimentService = Depends(get_sentiment_service),
) -> FearGreedTrendResponse:
    return service.get_fear_greed_trend(range)


@router.get("/volatility/trend", response_model=VolatilityTrendResponse)
def get_volatility_trend(
    range: Literal["30d"] = "30d",
    service: SentimentService = Depends(get_sentiment_service),
) -> VolatilityTrendResponse:
    return service.get_volatility_trend(range)


@router.get("/breadth", response_model=BreadthOverview)
def get_breadth(service: SentimentService = Depends(get_sentiment_service)) -> BreadthOverview:
    return service.get_breadth()
