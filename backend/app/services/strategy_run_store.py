from __future__ import annotations

from threading import Lock

from app.schemas.strategy_lab import StrategyLabResultResponse


class StrategyRunStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._runs: dict[str, dict[str, object]] = {}

    def create(self, run_id: str) -> None:
        with self._lock:
            self._runs[run_id] = {"status": "queued", "message": None, "result": None}

    def mark_running(self, run_id: str) -> None:
        self._update(run_id, status="running")

    def mark_succeeded(self, run_id: str, result: StrategyLabResultResponse) -> None:
        self._update(run_id, status="succeeded", result=result, message=None)

    def mark_failed(self, run_id: str, message: str) -> None:
        self._update(run_id, status="failed", message=message)

    def get(self, run_id: str) -> dict[str, object] | None:
        with self._lock:
            record = self._runs.get(run_id)
            return dict(record) if record else None

    def _update(self, run_id: str, **updates: object) -> None:
        with self._lock:
            record = self._runs.get(run_id)
            if record is None:
                return
            record.update(updates)
