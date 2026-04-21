from __future__ import annotations

import ast
from typing import Any

from app.core.errors import InvalidParameterError


class SandboxService:
    _blocked_nodes = (
        ast.Import,
        ast.ImportFrom,
        ast.ClassDef,
        ast.Lambda,
        ast.While,
        ast.For,
        ast.AsyncFor,
        ast.With,
        ast.AsyncWith,
        ast.Try,
        ast.Raise,
        ast.Delete,
        ast.Global,
        ast.Nonlocal,
    )
    _allowed_calls = {
        "compare",
        "is_price_in_drawdown",
        "is_fng_rebound_from_extreme_fear",
        "all",
        "any",
    }

    def validate_code(self, code: str) -> None:
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            raise InvalidParameterError("generated code is invalid") from exc

        function_names = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
        if function_names != ["build_signal"]:
            raise InvalidParameterError("generated code must define a single build_signal function")

        for node in ast.walk(tree):
            if isinstance(node, self._blocked_nodes):
                raise InvalidParameterError("generated code contains blocked syntax")
            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in self._allowed_calls:
                    raise InvalidParameterError("generated code contains blocked function calls")
            if isinstance(node, ast.Attribute):
                raise InvalidParameterError("generated code cannot access attributes")

    def execute_signal(self, code: str, context: dict[str, Any]) -> bool:
        self.validate_code(code)
        namespace: dict[str, Any] = {}
        safe_globals = {
            "__builtins__": {},
            "compare": self._compare,
            "is_price_in_drawdown": self._is_price_in_drawdown,
            "is_fng_rebound_from_extreme_fear": self._is_fng_rebound_from_extreme_fear,
            "all": all,
            "any": any,
        }
        exec(code, safe_globals, namespace)
        build_signal = namespace.get("build_signal")
        if build_signal is None:
            raise InvalidParameterError("generated code did not define build_signal")
        return bool(build_signal(context))

    @staticmethod
    def _compare(value: Any, operator: str, threshold: Any, upper_threshold: Any = None) -> bool:
        if value is None:
            return False
        current = float(value)
        if operator == "lt":
            return current < float(threshold)
        if operator == "gt":
            return current > float(threshold)
        if operator == "between":
            return float(threshold) <= current <= float(upper_threshold)
        if operator == "up":
            return bool(threshold)
        if operator == "down":
            return not bool(threshold)
        return False

    @staticmethod
    def _is_price_in_drawdown(context: dict[str, Any], lookback_days: int = 20) -> bool:
        history = [float(value) for value in context.get("price_history", []) if value is not None]
        current_price = context.get("current_price")
        if current_price is None or len(history) < 2:
            return False
        lookback = history[-lookback_days:]
        return float(current_price) < max(lookback)

    @staticmethod
    def _is_fng_rebound_from_extreme_fear(context: dict[str, Any]) -> bool:
        current = context.get("fng")
        previous = context.get("previous_fng")
        if current is None or previous is None:
            return False
        return float(previous) <= 25 and float(current) > float(previous)
