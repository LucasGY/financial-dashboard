def test_valuation_timeline_contract_and_precision(client):
    response = client.get("/api/v1/valuation/timeline?index=SPX&window=1y")

    assert response.status_code == 200
    payload = response.json()
    assert payload["index_code"] == "SPX"
    assert payload["display_name"] == "S&P 500"
    assert payload["current_value"] == 18.4
    assert payload["percentile"] == 100.0
    assert payload["series"][1]["value"] is None


def test_valuation_timeline_returns_not_found_for_empty_window(client):
    response = client.get("/api/v1/valuation/timeline?index=NDX&window=1y")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "no valuation data found for index=NDX within window=1y",
        }
    }


def test_valuation_invalid_query_returns_unified_error(client):
    response = client.get("/api/v1/valuation/timeline?index=QQQ&window=2y")

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "INVALID_PARAMETER",
            "message": "index: Input should be 'SPX' or 'NDX'; window: Input should be '1y', '5y' or '10y'",
        }
    }


def test_valuation_overview_keeps_missing_index_nullable(client):
    response = client.get("/api/v1/valuation/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["spx"]["percentile_5y"] == 100.0
    assert payload["ndx"] is None
