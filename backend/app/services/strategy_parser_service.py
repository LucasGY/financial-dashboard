from __future__ import annotations

import re
from typing import Optional

from app.core.errors import InvalidParameterError
from app.schemas.strategy_lab import StrategyCondition, StrategySpec
from app.services.llm.providers.base import LLMProvider


class StrategyParserService:
    def __init__(self, llm_provider: Optional[LLMProvider] = None) -> None:
        self._llm_provider = llm_provider

    def parse(self, prompt: str, target_ticker: str, forward_windows: list[int]) -> StrategySpec:
        normalized = self._normalize(prompt)
        resolved_target_ticker = self._infer_target_ticker(normalized) or target_ticker
        logic_operator = "any" if any(token in normalized for token in (" 或 ", "或者", " or ")) else "all"
        holding_period_days = self._parse_holding_period(normalized) or max(forward_windows)

        conditions: list[StrategyCondition] = []
        parse_notes: list[str] = []
        unsupported_fragments: list[str] = []

        conditions.extend(self._parse_simple_threshold_conditions(normalized))
        valuation_condition = self._parse_valuation_condition(normalized)
        if valuation_condition:
            conditions.append(valuation_condition)
        breadth_conditions = self._parse_breadth_conditions(normalized, resolved_target_ticker)
        conditions.extend(breadth_conditions)

        if "极度恐惧回升" in normalized or ("回升" in normalized and ("恐贪" in normalized or "fng" in normalized)):
            conditions.append(
                StrategyCondition(
                    indicator="fng",
                    operator="fng_rebound_from_extreme_fear",
                    description="FNG 从极度恐惧回升",
                )
            )
        if "回撤" in normalized and ("价格" in normalized or "股价" in normalized or resolved_target_ticker.lower() in normalized):
            conditions.append(
                StrategyCondition(
                    indicator="price",
                    operator="price_drawdown",
                    description="价格处于 20 日高点回撤状态",
                )
            )

        if any(token in normalized for token in ("止盈", "止损", "做空", "仓位", "组合", "再平衡", "权重", "滑点", "手续费")):
            unsupported_fragments.append("prompt contains unsupported portfolio or execution instructions")

        if not conditions:
            raise InvalidParameterError("unable to parse a supported strategy from prompt")

        execution_mode = "sandbox" if any(item.operator in {"price_drawdown", "fng_rebound_from_extreme_fear"} for item in conditions) else "rules"

        if resolved_target_ticker != target_ticker:
            parse_notes.append(f"target ticker overridden by prompt: {target_ticker} -> {resolved_target_ticker}")
        if self._llm_provider and self._llm_provider.is_configured():
            parse_notes.append("llm provider configured; heuristic parser remained primary for v1 determinism")

        return StrategySpec(
            prompt=prompt,
            target_ticker=resolved_target_ticker,
            logic_operator=logic_operator,
            holding_period_days=holding_period_days,
            forward_windows=forward_windows,
            entry_conditions=conditions,
            execution_mode=execution_mode,
            parse_notes=parse_notes,
            unsupported_fragments=unsupported_fragments,
        )

    @staticmethod
    def _normalize(prompt: str) -> str:
        normalized = prompt.lower()
        normalized = normalized.replace("，", " ").replace("。", " ").replace("；", " ")
        normalized = normalized.replace("且", " 且 ").replace("并且", " 且 ")
        normalized = normalized.replace("大于等于", ">=").replace("小于等于", "<=")
        normalized = normalized.replace("大于", ">").replace("高于", ">").replace("超过", ">")
        normalized = normalized.replace("小于", "<").replace("低于", "<")
        return " ".join(normalized.split())

    @staticmethod
    def _parse_holding_period(prompt: str) -> Optional[int]:
        match = re.search(r"持有\s*(\d+)\s*(?:个?交易?日|天|日)?", prompt)
        return int(match.group(1)) if match else None

    @staticmethod
    def _infer_target_ticker(prompt: str) -> Optional[str]:
        explicit_ticker_patterns = (
            ("SPY", r"\bspy\b"),
            ("QQQ", r"\bqqq\b"),
            ("AAPL", r"\baapl\b"),
            ("MSFT", r"\bmsft\b"),
            ("AMZN", r"\bamzn\b"),
            ("GOOGL", r"\bgoogl\b"),
            ("META", r"\bmeta\b"),
            ("NVDA", r"\bnvda\b"),
            ("TSLA", r"\btsla\b"),
        )
        for ticker, pattern in explicit_ticker_patterns:
            if re.search(pattern, prompt):
                return ticker
        if any(token in prompt for token in ("纳指", "ndx", "nasdaq-100", "nasdaq 100")):
            return "QQQ"
        if any(token in prompt for token in ("标普", "spx", "s&p 500", "sp500")):
            return "SPY"
        return None

    def _parse_simple_threshold_conditions(self, prompt: str) -> list[StrategyCondition]:
        patterns = (
            (
                "cnn_fear_greed",
                r"(?:cnn\s*(?:fear\s*&?\s*greed|fear\s+and\s+greed)|fear\s*&?\s*greed|恐贪指数|cnn恐贪|fng)[^0-9<>=]*([<>])\s*(\d+(?:\.\d+)?)",
                "CNN Fear & Greed",
            ),
            ("vix", r"(?:\bvix\b|波动率)[^0-9<>=]*([<>])\s*(\d+(?:\.\d+)?)", "VIX"),
            ("vol_structure", r"(?:vvix\s*/\s*vix(?:\s*/\s*3\.5)?|波动率结构)[^0-9<>=]*([<>])\s*(\d+(?:\.\d+)?)", "VVIX/VIX/3.5"),
        )
        results: list[StrategyCondition] = []
        for indicator, pattern, description in patterns:
            for operator, threshold in re.findall(pattern, prompt):
                results.append(
                    StrategyCondition(
                        indicator=indicator,
                        operator="gt" if operator == ">" else "lt",
                        threshold=float(threshold),
                        description=f"{description} {operator} {threshold}",
                    )
                )
        return self._apply_consecutive_days(prompt, results)

    def _parse_breadth_conditions(self, prompt: str, target_ticker: str) -> list[StrategyCondition]:
        conditions: list[StrategyCondition] = []
        for token_group, index_code in (
            (("sp500", "spx", "标普", "s&p 500"), "SPX"),
            (("ndx", "nasdaq-100", "nasdaq 100", "纳指"), "NDX"),
        ):
            if not any(token in prompt for token in token_group) and "breadth" not in prompt and "广度" not in prompt:
                continue
            period = 20
            period_match = re.search(r"(20|50|200)\s*(?:d|日)", prompt)
            if period_match:
                period = int(period_match.group(1))
            threshold_match = re.search(r"(?:广度|breadth|均线以上)[^0-9<>=]*([<>])\s*(\d+(?:\.\d+)?)", prompt)
            if threshold_match:
                operator, threshold = threshold_match.groups()
                conditions.append(
                    StrategyCondition(
                        indicator="breadth",
                        operator="gt" if operator == ">" else "lt",
                        threshold=float(threshold),
                        index_code=index_code,
                        breadth_period=period,
                        description=f"{index_code} breadth {period}d {operator} {threshold}",
                    )
                )
        if conditions:
            return self._apply_consecutive_days(prompt, conditions)
        if "breadth" in prompt or "广度" in prompt:
            inferred_index = "NDX" if target_ticker == "QQQ" else "SPX"
            threshold_match = re.search(r"(?:广度|breadth|均线以上)[^0-9<>=]*([<>])\s*(\d+(?:\.\d+)?)", prompt)
            if threshold_match:
                operator, threshold = threshold_match.groups()
                return [
                    StrategyCondition(
                        indicator="breadth",
                        operator="gt" if operator == ">" else "lt",
                        threshold=float(threshold),
                        index_code=inferred_index,
                        breadth_period=20,
                        description=f"{inferred_index} breadth 20d {operator} {threshold}",
                    )
                ]
        return []

    def _parse_valuation_condition(self, prompt: str) -> Optional[StrategyCondition]:
        if "估值" not in prompt and "pe" not in prompt and "ntm" not in prompt:
            return None
        index_code = None
        if any(token in prompt for token in ("spx", "标普", "s&p 500")):
            index_code = "SPX"
        elif any(token in prompt for token in ("ndx", "纳指", "nasdaq-100", "nasdaq 100")):
            index_code = "NDX"
        if index_code is None:
            return None

        raw_threshold_match = re.search(r"(?:ntm\s*pe|pe\s*ntm|估值|市盈率)[^0-9<>=分位%]*([<>])\s*(\d+(?:\.\d+)?)", prompt)
        window_match = re.search(r"(1|5|10)\s*年", prompt)
        percentile_match = re.search(r"([<>])\s*(\d+(?:\.\d+)?)\s*(?:分位|%)", prompt)
        if window_match and percentile_match:
            operator, threshold = percentile_match.groups()
            return StrategyCondition(
                indicator="valuation_percentile",
                operator="gt" if operator == ">" else "lt",
                threshold=float(threshold),
                index_code=index_code,
                percentile_window=f"{window_match.group(1)}y",
                description=f"{index_code} valuation percentile {window_match.group(1)}y {operator} {threshold}",
            )
        if raw_threshold_match:
            operator, threshold = raw_threshold_match.groups()
            return StrategyCondition(
                indicator="ntm_pe",
                operator="gt" if operator == ">" else "lt",
                threshold=float(threshold),
                index_code=index_code,
                description=f"{index_code} NTM PE {operator} {threshold}",
            )
        return None

    @staticmethod
    def _apply_consecutive_days(prompt: str, conditions: list[StrategyCondition]) -> list[StrategyCondition]:
        match = re.search(r"连续\s*(\d+)\s*天", prompt)
        if not match:
            return conditions
        consecutive_days = int(match.group(1))
        return [item.model_copy(update={"consecutive_days": consecutive_days}) for item in conditions]
