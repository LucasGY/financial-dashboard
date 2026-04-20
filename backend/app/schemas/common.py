from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TimeSeriesPoint(APIModel):
    trade_date: date
    value: Optional[float]


class BreadthSnapshot(APIModel):
    index_code: str
    display_name: str
    as_of_date: date
    above_20d_pct: Optional[float]
    above_50d_pct: Optional[float]
    above_200d_pct: Optional[float]
