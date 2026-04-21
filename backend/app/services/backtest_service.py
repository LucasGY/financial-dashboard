from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from statistics import median
from typing import Optional

from app.core.errors import NotFoundError
from app.core.precision import quantize_optional
from app.repositories.price_repository import PriceRepository
from app.repositories.strategy_feature_repository import StrategyFeatureRepository
from app.repositories.models import BreadthRow, FearGreedRow, PriceRow, ValuationRow, VixRow
from app.schemas.common import TimeSeriesPoint
from app.schemas.strategy_lab import (
    DataCoverage,
    SignalEvent,
    SignalMarkerPoint,
    StrategyCharts,
    StrategyCondition,
    StrategyLabResultResponse,
    StrategySpec,
    SummaryMetric,
)
from app.services.sandbox_service import SandboxService


VALUATION_INDEX_NAME_BY_CODE = {
    "SPX": "S&P 500 - PE - NTM",
    "NDX": "NASDAQ-100 - PE - NTM",
}

SUPPORTED_BREADTH_NAMES = {
    "SPX": "SP500",
    "NDX": "NDX100",
}

WINDOW_DAY_LOOKUP = {"1y": 365, "5y": 365 * 5, "10y": 365 * 10}


class BacktestService:
    def __init__(
        self,
        price_repository: PriceRepository,
        strategy_feature_repository: StrategyFeatureRepository,
        sandbox_service: SandboxService,
    ) -> None:
        self._price_repository = price_repository
        self._strategy_feature_repository = strategy_feature_repository
        self._sandbox_service = sandbox_service

    def execute(
        self,
        run_id: str,
        strategy_spec: StrategySpec,
        generated_code: str,
        start_date: date,
        end_date: date,
    ) -> StrategyLabResultResponse:
        history_start = start_date - timedelta(days=365 * 10 + 30)
        end_with_future = end_date + timedelta(days=max(strategy_spec.forward_windows) * 3)

        price_rows = self._price_repository.fetch_series([strategy_spec.target_ticker], history_start, end_with_future)
        if not price_rows:
            raise NotFoundError(f"no price data found for ticker={strategy_spec.target_ticker}")

        price_state = self._build_price_state(price_rows)
        signal_dates = [item for item in price_state["dates"] if start_date <= item <= end_date]
        if not signal_dates:
            raise NotFoundError(f"no trading dates found for ticker={strategy_spec.target_ticker} within requested range")

        features = self._load_feature_state(history_start, end_date)
        signal_events, summary_metrics, charts, coverage, warnings = self._run_backtest(
            strategy_spec=strategy_spec,
            generated_code=generated_code,
            signal_dates=signal_dates,
            price_state=price_state,
            features=features,
        )

        return StrategyLabResultResponse(
            run_id=run_id,
            strategy_spec=strategy_spec,
            generated_code=generated_code,
            summary_metrics=summary_metrics,
            signal_events=signal_events,
            charts=charts,
            data_coverage=coverage,
            warnings=warnings,
        )

    def _load_feature_state(self, start_date: date, end_date: date) -> dict[str, object]:
        fng_rows = self._strategy_feature_repository.fetch_fng_series(start_date, end_date)
        vix_rows = self._strategy_feature_repository.fetch_vix_series(start_date, end_date)
        breadth_rows = self._strategy_feature_repository.fetch_breadth_series(
            start_date,
            end_date,
            list(SUPPORTED_BREADTH_NAMES.values()),
        )
        valuation_rows = self._strategy_feature_repository.fetch_valuation_series(
            start_date,
            end_date,
            list(VALUATION_INDEX_NAME_BY_CODE.values()),
        )
        return {
            "fng_rows": fng_rows,
            "vix_rows": vix_rows,
            "breadth_rows": breadth_rows,
            "valuation_rows": valuation_rows,
            "fng_map": {item.trade_date: item.fng_value for item in fng_rows},
            "vix_map": {item.trade_date: item.vix_close for item in vix_rows},
            "vol_structure_map": {
                item.trade_date: self._compute_vol_structure(item.vvix_close, item.vix_close) for item in vix_rows
            },
            "breadth_map": self._build_breadth_map(breadth_rows),
            "valuation_map": self._build_valuation_map(valuation_rows),
        }

    @staticmethod
    def _build_price_state(price_rows: list[PriceRow]) -> dict[str, object]:
        dates = [item.trade_date for item in price_rows]
        closes = [float(item.adj_close_price) for item in price_rows]
        return {
            "dates": dates,
            "closes": closes,
            "date_to_index": {trade_date: index for index, trade_date in enumerate(dates)},
        }

    @staticmethod
    def _build_breadth_map(rows: list[BreadthRow]) -> dict[str, dict[date, dict[int, Optional[Decimal]]]]:
        result: dict[str, dict[date, dict[int, Optional[Decimal]]]] = defaultdict(dict)
        reverse_index = {value: key for key, value in SUPPORTED_BREADTH_NAMES.items()}
        for row in rows:
            index_code = reverse_index.get(row.index_name)
            if index_code is None:
                continue
            result[index_code][row.trade_date] = {
                20: row.above_20d_pct,
                50: row.above_50d_pct,
                200: row.above_200d_pct,
            }
        return result

    @staticmethod
    def _build_valuation_map(rows: list[ValuationRow]) -> dict[str, list[tuple[date, Decimal]]]:
        reverse_map = {value: key for key, value in VALUATION_INDEX_NAME_BY_CODE.items()}
        result: dict[str, list[tuple[date, Decimal]]] = defaultdict(list)
        for row in rows:
            index_code = reverse_map.get(row.index_name)
            if index_code is None or row.pe_ntm is None:
                continue
            result[index_code].append((row.trade_date, row.pe_ntm))
        return result

    def _run_backtest(
        self,
        strategy_spec: StrategySpec,
        generated_code: str,
        signal_dates: list[date],
        price_state: dict[str, object],
        features: dict[str, object],
    ) -> tuple[list[SignalEvent], list[SummaryMetric], StrategyCharts, DataCoverage, list[str]]:
        dates = price_state["dates"]
        closes = price_state["closes"]
        date_to_index = price_state["date_to_index"]
        window_returns: dict[int, list[float]] = {item: [] for item in strategy_spec.forward_windows}
        signal_events: list[SignalEvent] = []
        signal_points: list[SignalMarkerPoint] = []
        warnings: list[str] = []
        missing_features: set[str] = set()
        truncated_signal_count = 0

        for current_date in signal_dates:
            current_index = date_to_index[current_date]
            met_conditions: list[str] = []
            contexts = self._build_context(current_date, current_index, dates, closes, features)

            if strategy_spec.execution_mode == "sandbox":
                should_signal = self._sandbox_service.execute_signal(generated_code, contexts)
                if should_signal:
                    met_conditions = [item.description for item in strategy_spec.entry_conditions]
            else:
                evaluations: list[Optional[bool]] = []
                for condition in strategy_spec.entry_conditions:
                    evaluation = self._evaluate_condition(condition, current_index, dates, closes, features)
                    if evaluation is None:
                        missing_features.add(condition.indicator)
                    evaluations.append(evaluation)
                    if evaluation:
                        met_conditions.append(condition.description)
                filtered = [item is True for item in evaluations]
                should_signal = all(filtered) if strategy_spec.logic_operator == "all" else any(filtered)

            if not should_signal:
                continue

            forward_returns: dict[str, Optional[float]] = {}
            entry_index = current_index + 1
            entry_date = dates[entry_index] if entry_index < len(dates) else None
            entry_price = closes[entry_index] if entry_index < len(closes) else None

            for window in strategy_spec.forward_windows:
                exit_index = entry_index + window - 1
                if entry_price is None or exit_index >= len(closes):
                    forward_returns[str(window)] = None
                    continue
                exit_price = closes[exit_index]
                pct_return = ((exit_price / entry_price) - 1) * 100
                rounded_return = round(pct_return, 2)
                forward_returns[str(window)] = rounded_return
                window_returns[window].append(rounded_return)

            if any(forward_returns[str(item)] is None for item in strategy_spec.forward_windows):
                truncated_signal_count += 1

            signal_events.append(
                SignalEvent(
                    signal_date=current_date,
                    entry_date=entry_date,
                    forward_returns=forward_returns,
                    met_conditions=met_conditions,
                )
            )
            signal_points.append(
                SignalMarkerPoint(
                    trade_date=current_date,
                    price=round(closes[current_index], 2),
                    label=f"Signal {current_date.isoformat()}",
                )
            )

        if not signal_events:
            warnings.append("当前策略在所选区间内没有触发任何有效信号。")
        if "breadth" in missing_features:
            warnings.append("Breadth 样本较短，相关条件可能显著压缩有效样本。")
        if strategy_spec.unsupported_fragments:
            warnings.append("Prompt 包含首版未支持的执行语义，结果按受控子集解释。")

        summary_metrics = [self._summarize_window(window, window_returns[window]) for window in strategy_spec.forward_windows]
        charts = StrategyCharts(
            win_rate_bars=[
                TimeSeriesBarFactory.make(label=f"{item.window_days}D", value=item.win_rate) for item in summary_metrics
            ],
            avg_return_bars=[
                TimeSeriesBarFactory.make(label=f"{item.window_days}D", value=item.avg_return) for item in summary_metrics
            ],
            price_series=[
                TimeSeriesPoint(trade_date=trade_date, value=round(close, 2))
                for trade_date, close in zip(signal_dates, [closes[date_to_index[item]] for item in signal_dates])
            ],
            signal_points=signal_points,
        )
        coverage = DataCoverage(
            available_start_date=signal_dates[0] if signal_dates else None,
            available_end_date=signal_dates[-1] if signal_dates else None,
            feature_start_date=self._feature_start_date(strategy_spec, features),
            feature_end_date=self._feature_end_date(strategy_spec, features),
            missing_features=sorted(missing_features),
            truncated_signal_count=truncated_signal_count,
        )
        return signal_events, summary_metrics, charts, coverage, warnings

    def _build_context(
        self,
        current_date: date,
        current_index: int,
        dates: list[date],
        closes: list[float],
        features: dict[str, object],
    ) -> dict[str, object]:
        price_history = closes[: current_index + 1]
        fng_map = features["fng_map"]
        vix_map = features["vix_map"]
        vol_structure_map = features["vol_structure_map"]
        breadth_map = features["breadth_map"]

        context: dict[str, object] = {
            "current_price": closes[current_index],
            "price_history": price_history,
            "fng": self._decimal_to_float(fng_map.get(current_date)),
            "cnn_fear_greed": self._decimal_to_float(fng_map.get(current_date)),
            "previous_fng": self._decimal_to_float(fng_map.get(dates[current_index - 1])) if current_index > 0 else None,
            "vix": self._decimal_to_float(vix_map.get(current_date)),
            "vol_structure": self._decimal_to_float(vol_structure_map.get(current_date)),
        }
        for index_code, date_map in breadth_map.items():
            period_map = date_map.get(current_date, {})
            for period, value in period_map.items():
                context[f"{index_code.lower()}_breadth_{period}d"] = self._decimal_to_float(value)
        for index_code in VALUATION_INDEX_NAME_BY_CODE:
            context[f"{index_code.lower()}_ntm_pe"] = self._valuation_raw_value(
                features["valuation_map"], index_code, current_date
            )
            for window in WINDOW_DAY_LOOKUP:
                context[f"{index_code.lower()}_valuation_percentile_{window}"] = self._valuation_percentile(
                    features["valuation_map"], index_code, current_date, window
                )
        return context

    def _evaluate_condition(
        self,
        condition: StrategyCondition,
        current_index: int,
        dates: list[date],
        closes: list[float],
        features: dict[str, object],
    ) -> Optional[bool]:
        if condition.operator == "price_drawdown":
            lookback = closes[max(0, current_index - 19) : current_index + 1]
            if len(lookback) < 2:
                return None
            return closes[current_index] < max(lookback)

        if condition.operator == "fng_rebound_from_extreme_fear":
            if current_index == 0:
                return None
            fng_map = features["fng_map"]
            current = fng_map.get(dates[current_index])
            previous = fng_map.get(dates[current_index - 1])
            if current is None or previous is None:
                return None
            return current > previous and previous <= 25

        if condition.indicator == "valuation_percentile":
            value = self._valuation_percentile(features["valuation_map"], condition.index_code or "", dates[current_index], condition.percentile_window or "5y")
        elif condition.indicator == "ntm_pe":
            value = self._valuation_raw_value(features["valuation_map"], condition.index_code or "", dates[current_index])
        elif condition.indicator == "breadth":
            period_map = features["breadth_map"].get(condition.index_code or "", {}).get(dates[current_index])
            value = self._decimal_to_float(period_map.get(condition.breadth_period or 20)) if period_map else None
        elif condition.indicator in {"fng", "cnn_fear_greed"}:
            value = self._decimal_to_float(features["fng_map"].get(dates[current_index]))
        elif condition.indicator == "vix":
            value = self._decimal_to_float(features["vix_map"].get(dates[current_index]))
        else:
            value = self._decimal_to_float(features["vol_structure_map"].get(dates[current_index]))

        if value is None:
            return None

        if condition.consecutive_days <= 1:
            return self._compare_value(value, condition)

        for index in range(current_index - condition.consecutive_days + 1, current_index + 1):
            if index < 0:
                return None
            comparison = self._evaluate_condition(
                condition.model_copy(update={"consecutive_days": 1}),
                index,
                dates,
                closes,
                features,
            )
            if comparison is not True:
                return comparison
        return True

    @staticmethod
    def _compare_value(value: float, condition: StrategyCondition) -> bool:
        if condition.operator == "lt":
            return value < float(condition.threshold or 0)
        if condition.operator == "gt":
            return value > float(condition.threshold or 0)
        if condition.operator == "between":
            return float(condition.threshold or 0) <= value <= float(condition.upper_threshold or 0)
        return False

    def _valuation_percentile(
        self,
        valuation_map: dict[str, list[tuple[date, Decimal]]],
        index_code: str,
        current_date: date,
        window: str,
    ) -> Optional[float]:
        rows = valuation_map.get(index_code, [])
        if not rows:
            return None
        cutoff = current_date - timedelta(days=WINDOW_DAY_LOOKUP[window])
        values = [value for trade_date, value in rows if cutoff <= trade_date <= current_date]
        current_value = next((value for trade_date, value in reversed(rows) if trade_date <= current_date), None)
        if current_value is None or not values:
            return None
        below_or_equal = sum(1 for value in values if value <= current_value)
        return round((below_or_equal / len(values)) * 100, 2)

    def _valuation_raw_value(
        self,
        valuation_map: dict[str, list[tuple[date, Decimal]]],
        index_code: str,
        current_date: date,
    ) -> Optional[float]:
        rows = valuation_map.get(index_code, [])
        current_value = next((value for trade_date, value in reversed(rows) if trade_date <= current_date), None)
        return self._decimal_to_float(current_value)

    def _feature_start_date(self, strategy_spec: StrategySpec, features: dict[str, object]) -> Optional[date]:
        starts: list[date] = []
        for condition in strategy_spec.entry_conditions:
            if condition.indicator in {"fng", "cnn_fear_greed"} and features["fng_rows"]:
                starts.append(features["fng_rows"][0].trade_date)
            if condition.indicator in {"vix", "vol_structure"} and features["vix_rows"]:
                starts.append(features["vix_rows"][0].trade_date)
            if condition.indicator == "breadth":
                index_rows = [item.trade_date for item in features["breadth_rows"] if item.index_name == SUPPORTED_BREADTH_NAMES.get(condition.index_code or "")]
                if index_rows:
                    starts.append(index_rows[0])
            if condition.indicator in {"valuation_percentile", "ntm_pe"}:
                valuation_rows = [item[0] for item in features["valuation_map"].get(condition.index_code or "", [])]
                if valuation_rows:
                    starts.append(valuation_rows[0])
        return max(starts) if starts else None

    def _feature_end_date(self, strategy_spec: StrategySpec, features: dict[str, object]) -> Optional[date]:
        ends: list[date] = []
        for condition in strategy_spec.entry_conditions:
            if condition.indicator in {"fng", "cnn_fear_greed"} and features["fng_rows"]:
                ends.append(features["fng_rows"][-1].trade_date)
            if condition.indicator in {"vix", "vol_structure"} and features["vix_rows"]:
                ends.append(features["vix_rows"][-1].trade_date)
            if condition.indicator == "breadth":
                index_rows = [item.trade_date for item in features["breadth_rows"] if item.index_name == SUPPORTED_BREADTH_NAMES.get(condition.index_code or "")]
                if index_rows:
                    ends.append(index_rows[-1])
            if condition.indicator in {"valuation_percentile", "ntm_pe"}:
                valuation_rows = [item[0] for item in features["valuation_map"].get(condition.index_code or "", [])]
                if valuation_rows:
                    ends.append(valuation_rows[-1])
        return min(ends) if ends else None

    @staticmethod
    def _compute_vol_structure(vvix_close: Optional[Decimal], vix_close: Optional[Decimal]) -> Optional[Decimal]:
        if vvix_close is None or vix_close in (None, Decimal("0")):
            return None
        return vvix_close / vix_close / Decimal("3.5")

    @staticmethod
    def _summarize_window(window: int, returns: list[float]) -> SummaryMetric:
        if not returns:
            return SummaryMetric(
                window_days=window,
                signal_count=0,
                win_rate=None,
                avg_return=None,
                median_return=None,
                max_return=None,
                min_return=None,
            )
        wins = sum(1 for item in returns if item > 0)
        avg_return = round(sum(returns) / len(returns), 2)
        return SummaryMetric(
            window_days=window,
            signal_count=len(returns),
            win_rate=round((wins / len(returns)) * 100, 2),
            avg_return=avg_return,
            median_return=round(median(returns), 2),
            max_return=max(returns),
            min_return=min(returns),
        )

    @staticmethod
    def _decimal_to_float(value: Optional[Decimal | int | float]) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return quantize_optional(value, 4)
        return float(value)


class TimeSeriesBarFactory:
    @staticmethod
    def make(label: str, value: Optional[float]):
        from app.schemas.strategy_lab import ChartBarPoint

        return ChartBarPoint(label=label, value=value)
