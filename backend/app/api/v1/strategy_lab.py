from fastapi import APIRouter, Depends

from app.api.dependencies import get_strategy_lab_service
from app.schemas.strategy_lab import StrategyLabResultResponse, StrategyLabRunRequest, StrategyRunResponse
from app.services.strategy_lab_service import StrategyLabService

router = APIRouter()


@router.post("/runs", response_model=StrategyRunResponse)
def create_run(
    request: StrategyLabRunRequest,
    service: StrategyLabService = Depends(get_strategy_lab_service),
) -> StrategyRunResponse:
    return service.create_run(request)


@router.get("/runs/{run_id}", response_model=StrategyRunResponse)
def get_run_status(
    run_id: str,
    service: StrategyLabService = Depends(get_strategy_lab_service),
) -> StrategyRunResponse:
    return service.get_run_status(run_id)


@router.get("/runs/{run_id}/result", response_model=StrategyLabResultResponse)
def get_run_result(
    run_id: str,
    service: StrategyLabService = Depends(get_strategy_lab_service),
) -> StrategyLabResultResponse:
    return service.get_run_result(run_id)
