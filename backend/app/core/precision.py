from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


def quantize_optional(value: Optional[Decimal], places: int) -> Optional[float]:
    if value is None:
        return None
    quantizer = Decimal("1").scaleb(-places)
    return float(value.quantize(quantizer, rounding=ROUND_HALF_UP))
