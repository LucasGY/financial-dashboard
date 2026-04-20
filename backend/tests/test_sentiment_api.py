from decimal import Decimal

from app.repositories.models import FearGreedRow, VixRow
from app.services.sentiment_service import SentimentService


def test_sentiment_overview_contract(client):
    response = client.get("/api/v1/sentiment/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["fear_greed"] == {
        "as_of_date": "2026-04-18",
        "value": 21,
        "label": "Extreme Fear",
        "color": "dark_green",
        "day_change": -3,
    }
    assert payload["vix"] == {"as_of_date": "2026-04-18", "value": 18.32}
    assert payload["breadth"]["spx"]["above_20d_pct"] == 82.12
    assert payload["breadth"]["spx"]["above_200d_pct"] is None


def test_volatility_trend_handles_null_and_zero(client):
    response = client.get("/api/v1/sentiment/volatility/trend?range=30d")

    assert response.status_code == 200
    payload = response.json()
    assert payload["vix_current"] == 18.32
    assert payload["vol_structure_series"][1]["value"] is None
    assert payload["vol_structure_current"] == 1.8629


def test_invalid_sentiment_range_returns_unified_error(client):
    response = client.get("/api/v1/sentiment/fear-greed/trend?range=90d")

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "INVALID_PARAMETER",
            "message": "range: Input should be '30d'",
        }
    }


def test_sentiment_service_null_latest_snapshot():
    service = SentimentService(
        raw_fng_repository=type("Repo", (), {"fetch_latest": lambda self, limit: [FearGreedRow(trade_date=__import__('datetime').date(2026, 4, 18), fng_value=None)], "fetch_recent": lambda self, limit: []})(),
        raw_vix_repository=type("VixRepo", (), {"fetch_latest": lambda self, limit: [VixRow(trade_date=__import__('datetime').date(2026, 4, 18), vix_close=Decimal("10.00"), vvix_close=None)], "fetch_recent": lambda self, limit: []})(),
        market_breadth_repository=type("BreadthRepo", (), {"fetch_latest_snapshots": lambda self: []})(),
    )

    overview = service.get_overview()
    assert overview.fear_greed.value is None
    assert overview.fear_greed.label is None
    assert overview.vol_structure.value is None
