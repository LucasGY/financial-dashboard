from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from statistics import median
from typing import Optional

from app.core.errors import NotFoundError
from app.core.precision import quantize_optional
from app.repositories.models import BreadthRow, PriceRow, ValuationRow
from app.repositories.price_repository import PriceRepository
from app.repositories.strategy_feature_repository import StrategyFeatureRepository
from app.schemas.market_regime import (
    MarketRegimeCondition,
    MarketRegimeMetric,
    MarketRegimeOverviewResponse,
    MarketRegimeStatsResponse,
)
from app.services.backtest_service import SUPPORTED_BREADTH_NAMES, VALUATION_INDEX_NAME_BY_CODE


INDEX_BY_TICKER = {
    "SPY": "SPX",
    "QQQ": "NDX",
}

FORWARD_WINDOWS = [5, 30, 90, 252]
WINDOW_DAYS = {
    "1y": 365,
    "5y": 365 * 5,
    "10y": 365 * 10,
}
FEATURE_BUFFER_DAYS = 365
NEAREST_SAMPLE_COUNTS = {
    "1y": 20,
    "5y": 50,
    "10y": 100,
}
PERCENTILE_WEIGHTS = {
    "Fear & Greed": 1 / 6,
    "VIX": 1 / 6,
    "50D Breadth": 1 / 6,
    "NTM PE": 0.5,
}


class MarketRegimeService:
    def __init__(
        self,
        price_repository: PriceRepository,
        strategy_feature_repository: StrategyFeatureRepository,
    ) -> None:
        self._price_repository = price_repository
        self._strategy_feature_repository = strategy_feature_repository

    def get_overview(self, window: str = "1y") -> MarketRegimeOverviewResponse:
        today = date.today()
        price_start_date = today - timedelta(days=WINDOW_DAYS[window])
        feature_start_date = price_start_date - timedelta(days=FEATURE_BUFFER_DAYS)
        tickers = list(INDEX_BY_TICKER)

        price_rows = self._price_repository.fetch_series(tickers, price_start_date, today)
        if not price_rows:
            raise NotFoundError("no price data found for market regime tickers")

        latest_date = max(item.trade_date for item in price_rows)
        feature_state = self._load_features(feature_start_date, latest_date)
        prices_by_ticker: dict[str, list[PriceRow]] = {
            ticker: [item for item in price_rows if item.ticker == ticker] for ticker in tickers
        }

        return MarketRegimeOverviewResponse(
            window=window,
            items=[
                self._build_stats_from_state(ticker, prices_by_ticker.get(ticker, []), feature_state, window)
                for ticker in tickers
            ]
        )

    def get_stats(self, ticker: str, window: str = "1y") -> MarketRegimeStatsResponse:
        target_ticker = ticker.upper()
        today = date.today()
        price_start_date = today - timedelta(days=WINDOW_DAYS[window])
        feature_start_date = price_start_date - timedelta(days=FEATURE_BUFFER_DAYS)

        price_rows = self._price_repository.fetch_series([target_ticker], price_start_date, today)
        if not price_rows:
            raise NotFoundError(f"no price data found for ticker={target_ticker}")

        feature_state = self._load_features(feature_start_date, price_rows[-1].trade_date)
        return self._build_stats_from_state(target_ticker, price_rows, feature_state, window)

    def _build_stats_from_state(
        self,
        target_ticker: str,
        price_rows: list[PriceRow],
        feature_state: dict[str, object],
        window: str,
    ) -> MarketRegimeStatsResponse:
        index_code = INDEX_BY_TICKER[target_ticker]
        if not price_rows:
            raise NotFoundError(f"no price data found for ticker={target_ticker}")

        prices = self._build_price_state(price_rows)
        latest_date = prices["dates"][-1]
        latest_price = prices["closes"][-1]
        snapshots = {
            trade_date: self._build_snapshot(index_code, trade_date, feature_state)
            for trade_date in prices["dates"]
        }
        percentile_maps = self._build_percentile_maps(snapshots)
        latest_snapshot = snapshots[latest_date]
        missing = [label for label, value in latest_snapshot.items() if value is None]

        warnings: list[str] = []
        if missing:
            warnings.append(f"最新交易日缺少这些特征，无法完整匹配历史状态：{', '.join(missing)}。")

        current_percentiles = self._build_percentile_signature(latest_date, latest_snapshot, percentile_maps)
        returns_by_window: dict[int, list[float]] = {w: [] for w in FORWARD_WINDOWS}

        if not missing:
            dates: list[date] = prices["dates"]
            closes: list[float] = prices["closes"]
            candidates: list[tuple[float, int]] = []
            for index, signal_date in enumerate(dates[:-1]):
                snapshot = snapshots[signal_date]
                percentile_signature = self._build_percentile_signature(signal_date, snapshot, percentile_maps)
                distance = self._percentile_distance(percentile_signature, current_percentiles)
                if distance is None:
                    continue
                candidates.append((distance, index))

            sample_count = NEAREST_SAMPLE_COUNTS[window]
            nearest_indices = [index for _, index in sorted(candidates, key=lambda item: (item[0], -item[1]))[:sample_count]]
            for index in nearest_indices:
                entry_price = closes[index]
                for forward_window in FORWARD_WINDOWS:
                    exit_index = index + forward_window
                    if exit_index >= len(closes):
                        continue
                    returns_by_window[forward_window].append(round(((closes[exit_index] / entry_price) - 1) * 100, 2))

        metrics = [self._summarize_window(fw, returns_by_window[fw]) for fw in FORWARD_WINDOWS]
        if not any(metric.signal_count for metric in metrics) and not missing:
            warnings.append("历史上没有找到具备完整远期价格的相似样本。")

        return MarketRegimeStatsResponse(
            ticker=target_ticker,
            index_code=index_code,
            window=window,
            as_of_date=latest_date,
            entry_price=round(latest_price, 2),
            conditions=self._build_conditions(latest_snapshot, current_percentiles),
            metrics=metrics,
            warnings=warnings,
        )

    def _load_features(self, start_date: date, end_date: date) -> dict[str, object]:
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
            "fng_map": {item.trade_date: item.fng_value for item in fng_rows},
            "vix_map": {item.trade_date: item.vix_close for item in vix_rows},
            "breadth_map": self._build_breadth_map(breadth_rows),
            "valuation_map": self._build_valuation_map(valuation_rows),
        }

    @staticmethod
    def _build_price_state(price_rows: list[PriceRow]) -> dict[str, list]:
        return {
            "dates": [item.trade_date for item in price_rows],
            "closes": [float(item.adj_close_price) for item in price_rows],
        }

    @staticmethod
    def _build_breadth_map(rows: list[BreadthRow]) -> dict[str, dict[date, Optional[Decimal]]]:
        result: dict[str, dict[date, Optional[Decimal]]] = defaultdict(dict)
        reverse_index = {value: key for key, value in SUPPORTED_BREADTH_NAMES.items()}
        for row in rows:
            index_code = reverse_index.get(row.index_name)
            if index_code is not None:
                result[index_code][row.trade_date] = row.above_50d_pct
        return result

    @staticmethod
    def _build_valuation_map(rows: list[ValuationRow]) -> dict[str, list[tuple[date, Decimal]]]:
        reverse_map = {value: key for key, value in VALUATION_INDEX_NAME_BY_CODE.items()}
        result: dict[str, list[tuple[date, Decimal]]] = defaultdict(list)
        for row in rows:
            index_code = reverse_map.get(row.index_name)
            if index_code is not None and row.pe_ntm is not None:
                result[index_code].append((row.trade_date, row.pe_ntm))
        return result

    def _build_snapshot(self, index_code: str, current_date: date, feature_state: dict[str, object]) -> dict[str, Optional[float]]:
        valuation_map = feature_state["valuation_map"]
        pe_value = self._valuation_raw_value(valuation_map, index_code, current_date)
        return {
            "Fear & Greed": self._to_float(feature_state["fng_map"].get(current_date)),
            "VIX": self._to_float(feature_state["vix_map"].get(current_date)),
            "50D Breadth": self._to_float(feature_state["breadth_map"].get(index_code, {}).get(current_date)),
            "NTM PE": pe_value,
        }

    @staticmethod
    def _build_percentile_maps(snapshots: dict[date, dict[str, Optional[float]]]) -> dict[str, dict[date, float]]:
        percentile_maps: dict[str, dict[date, float]] = {}
        keys = ["Fear & Greed", "VIX", "50D Breadth", "NTM PE"]
        for key in keys:
            values = [
                (trade_date, snapshot[key])
                for trade_date, snapshot in snapshots.items()
                if snapshot[key] is not None
            ]
            sorted_values = sorted(float(value) for _, value in values if value is not None)
            date_percentiles: dict[date, float] = {}
            for trade_date, value in values:
                if value is None:
                    continue
                date_percentiles[trade_date] = percentile_score(float(value), sorted_values)
            percentile_maps[key] = date_percentiles
        return percentile_maps

    @staticmethod
    def _build_percentile_signature(
        trade_date: date,
        snapshot: dict[str, Optional[float]],
        percentile_maps: dict[str, dict[date, float]],
    ) -> dict[str, Optional[float]]:
        return {
            key: percentile_maps[key].get(trade_date) if snapshot[key] is not None else None
            for key in ["Fear & Greed", "VIX", "50D Breadth", "NTM PE"]
        }

    @staticmethod
    def _percentile_distance(
        percentile_signature: dict[str, Optional[float]],
        current_percentiles: dict[str, Optional[float]],
    ) -> Optional[float]:
        if any(current_percentiles[key] is None or percentile_signature[key] is None for key in current_percentiles):
            return None
        return sum(
            abs(float(percentile_signature[key]) - float(current_percentiles[key])) * PERCENTILE_WEIGHTS[key]
            for key in current_percentiles
        )

    @staticmethod
    def _build_conditions(
        snapshot: dict[str, Optional[float]],
        current_percentiles: dict[str, Optional[float]],
    ) -> list[MarketRegimeCondition]:
        return [
            MarketRegimeService._condition("fng", "Fear & Greed", snapshot["Fear & Greed"], None, current_percentiles["Fear & Greed"]),
            MarketRegimeService._condition("vix", "VIX", snapshot["VIX"], None, current_percentiles["VIX"]),
            MarketRegimeService._condition("breadth_50d", "50D Breadth", snapshot["50D Breadth"], "%", current_percentiles["50D Breadth"]),
            MarketRegimeService._condition("ntm_pe", "NTM PE", snapshot["NTM PE"], None, current_percentiles["NTM PE"]),
        ]

    @staticmethod
    def _condition(
        key: str,
        label: str,
        value: Optional[float],
        unit: Optional[str],
        percentile: Optional[float],
    ) -> MarketRegimeCondition:
        rounded_percentile = round(percentile, 1) if percentile is not None else None
        return MarketRegimeCondition(
            key=key,
            label=label,
            value=value,
            unit=unit,
            bucket=round(percentile) if percentile is not None else None,
            percentile=rounded_percentile,
            bucket_label=f"P{rounded_percentile}" if rounded_percentile is not None else "--",
        )

    def _valuation_raw_value(
        self,
        valuation_map: dict[str, list[tuple[date, Decimal]]],
        index_code: str,
        current_date: date,
    ) -> Optional[float]:
        rows = valuation_map.get(index_code, [])
        current_value = next((value for trade_date, value in reversed(rows) if trade_date <= current_date), None)
        return self._to_float(current_value)

    @staticmethod
    def _summarize_window(window: int, returns: list[float]) -> MarketRegimeMetric:
        if not returns:
            return MarketRegimeMetric(
                window_days=window,
                signal_count=0,
                win_rate=None,
                avg_return=None,
                median_return=None,
                max_return=None,
                min_return=None,
            )
        wins = sum(1 for item in returns if item > 0)
        return MarketRegimeMetric(
            window_days=window,
            signal_count=len(returns),
            win_rate=round((wins / len(returns)) * 100, 2),
            avg_return=round(sum(returns) / len(returns), 2),
            median_return=round(median(returns), 2),
            max_return=max(returns),
            min_return=min(returns),
        )

    @staticmethod
    def _to_float(value: Optional[Decimal | int | float]) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return quantize_optional(value, 4)
        return float(value)


def percentile_score(value: float, sorted_values: list[float]) -> float:
    if not sorted_values:
        return 0.0
    below_or_equal = 0
    for item in sorted_values:
        if item <= value:
            below_or_equal += 1
        else:
            break
    return round((below_or_equal / len(sorted_values)) * 100, 4)
