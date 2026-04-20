from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union

from app.core.errors import InvalidParameterError


INDEX_CONFIG = {
    "SPX": {
        "display_name": "S&P 500",
        "aliases": [
            "SPX",
            "SP500",
            "S&P 500",
            "S&P 500 Index",
            "S&P 500 - PE - NTM",
        ],
    },
    "NDX": {
        "display_name": "NASDAQ-100",
        "aliases": [
            "NDX",
            "NDX100",
            "NASDAQ-100",
            "NASDAQ 100",
            "Nasdaq 100",
            "NASDAQ-100 - PE - NTM",
        ],
    },
}

BREADTH_INDEX_MAPPING = {
    "SP500": "SPX",
    "NDX100": "NDX",
}

FNG_BUCKETS = (
    (25, "Extreme Fear", "dark_green"),
    (45, "Fear", "green"),
    (55, "Neutral", "neutral"),
    (75, "Greed", "orange"),
    (100, "Extreme Greed", "red"),
)


def get_index_config(index_code: str) -> Dict[str, Union[str, List[str]]]:
    config = INDEX_CONFIG.get(index_code)
    if config is None:
        raise InvalidParameterError("index must be one of: SPX, NDX")
    return config


def map_breadth_index(index_name: str) -> Optional[str]:
    return BREADTH_INDEX_MAPPING.get(index_name)


def get_display_name(index_code: str) -> str:
    return str(get_index_config(index_code)["display_name"])


def get_index_aliases(index_code: str) -> list[str]:
    return list(get_index_config(index_code)["aliases"])


def map_fng_label_color(value: Optional[int]) -> Tuple[Optional[str], Optional[str]]:
    if value is None:
        return None, None
    for upper_bound, label, color in FNG_BUCKETS:
        if value <= upper_bound:
            return label, color
    return None, None
