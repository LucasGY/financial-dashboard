from typing import Literal

from fastapi import APIRouter, Depends

from app.api.dependencies import get_valuation_service
from app.schemas.valuation import ValuationOverviewResponse, ValuationTimelineResponse
from app.services.valuation_service import ValuationService

router = APIRouter()


@router.get("/timeline", response_model=ValuationTimelineResponse)
def get_timeline(
    index: Literal["SPX", "NDX"],
    window: Literal["1y", "5y", "10y"],
    service: ValuationService = Depends(get_valuation_service),
) -> ValuationTimelineResponse:
    return service.get_timeline(index, window)


@router.get("/overview", response_model=ValuationOverviewResponse)
def get_overview(service: ValuationService = Depends(get_valuation_service)) -> ValuationOverviewResponse:
    return service.get_overview()
