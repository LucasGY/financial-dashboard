from __future__ import annotations

from app.schemas.strategy_lab import StrategyCondition, StrategySpec


class StrategyCodegenService:
    def generate(self, strategy_spec: StrategySpec) -> str:
        lines = [
            "def build_signal(context):",
            f"    # target: {strategy_spec.target_ticker}",
        ]
        rendered_conditions = [self._render_condition(item) for item in strategy_spec.entry_conditions]
        joiner = " and " if strategy_spec.logic_operator == "all" else " or "
        expression = joiner.join(rendered_conditions) if rendered_conditions else "False"
        lines.append(f"    return {expression}")
        return "\n".join(lines)

    def _render_condition(self, condition: StrategyCondition) -> str:
        if condition.operator == "price_drawdown":
            return "is_price_in_drawdown(context, 20)"
        if condition.operator == "fng_rebound_from_extreme_fear":
            return "is_fng_rebound_from_extreme_fear(context)"

        context_key = self._context_key(condition)
        if condition.operator == "between":
            return (
                f"compare(context.get('{context_key}'), 'between', "
                f"{condition.threshold}, {condition.upper_threshold})"
            )
        return f"compare(context.get('{context_key}'), '{condition.operator}', {condition.threshold})"

    @staticmethod
    def _context_key(condition: StrategyCondition) -> str:
        if condition.indicator == "breadth":
            return f"{condition.index_code.lower()}_breadth_{condition.breadth_period}d"
        if condition.indicator == "ntm_pe":
            return f"{condition.index_code.lower()}_ntm_pe"
        if condition.indicator == "valuation_percentile":
            return f"{condition.index_code.lower()}_valuation_percentile_{condition.percentile_window}"
        return condition.indicator
