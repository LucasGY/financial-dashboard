from __future__ import annotations

from uuid import uuid4

from app.core.errors import InvalidParameterError, NotFoundError
from app.schemas.strategy_lab import StrategyLabResultResponse, StrategyLabRunRequest, StrategyRunResponse
from app.services.backtest_service import BacktestService
from app.services.strategy_codegen_service import StrategyCodegenService
from app.services.strategy_parser_service import StrategyParserService
from app.services.strategy_run_store import StrategyRunStore


class StrategyLabService:
    def __init__(
        self,
        parser_service: StrategyParserService,
        codegen_service: StrategyCodegenService,
        backtest_service: BacktestService,
        run_store: StrategyRunStore,
    ) -> None:
        self._parser_service = parser_service
        self._codegen_service = codegen_service
        self._backtest_service = backtest_service
        self._run_store = run_store

    def create_run(self, request: StrategyLabRunRequest) -> StrategyRunResponse:
        run_id = str(uuid4())
        self._run_store.create(run_id)
        self._run_store.mark_running(run_id)

        try:
            strategy_spec = self._parser_service.parse(
                prompt=request.prompt,
                target_ticker=request.target_ticker,
                forward_windows=request.forward_windows,
            )
            generated_code = self._codegen_service.generate(strategy_spec)
            result = self._backtest_service.execute(
                run_id=run_id,
                strategy_spec=strategy_spec,
                generated_code=generated_code,
                start_date=request.start_date,
                end_date=request.end_date,
            )
            self._run_store.mark_succeeded(run_id, result)
            return StrategyRunResponse(run_id=run_id, status="succeeded")
        except Exception as exc:
            message = str(exc)
            self._run_store.mark_failed(run_id, message)
            if isinstance(exc, (InvalidParameterError, NotFoundError)):
                return StrategyRunResponse(run_id=run_id, status="failed", message=message)
            raise

    def get_run_status(self, run_id: str) -> StrategyRunResponse:
        record = self._run_store.get(run_id)
        if record is None:
            raise NotFoundError(f"strategy run not found: {run_id}")
        return StrategyRunResponse(
            run_id=run_id,
            status=str(record["status"]),
            message=str(record["message"]) if record.get("message") else None,
        )

    def get_run_result(self, run_id: str) -> StrategyLabResultResponse:
        record = self._run_store.get(run_id)
        if record is None:
            raise NotFoundError(f"strategy run not found: {run_id}")
        if record.get("status") != "succeeded" or record.get("result") is None:
            raise InvalidParameterError(f"strategy run is not ready: {run_id}")
        return record["result"]
