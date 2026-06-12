def test_valuation_timeline_contract_and_precision(client):
    response = client.get("/api/v1/valuation/timeline?index=SPX&window=1y")

    assert response.status_code == 200
    payload = response.json()
    assert payload["index_code"] == "SPX"
    assert payload["display_name"] == "S&P 500"
    assert payload["current_value"] == 22.4
    assert payload["percentile"] == 100.0
    assert payload["estimated_date"] == "2026-04-08"
    assert payload["estimate_method"] == "proxy_adjusted"
    assert payload["valuation_source"] == "proxy_adjusted"
    assert payload["is_estimated"] is True
    assert payload["raw_pe_ntm"] == 22.0
    assert payload["based_on_trade_date"] == "2026-04-07"
    assert payload["proxy_ticker"] == "SP500"
    assert payload["proxy_return"] == 0.01818182
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


def test_price_attribution_contract(client):
    response = client.get("/api/v1/valuation/price-attribution?index=SPX&tag=week")

    assert response.status_code == 200
    payload = response.json()
    first = payload["series"][0]

    assert payload["index_code"] == "SPX"
    assert payload["ticker"] == "SPY"
    assert payload["tag"] == "week"
    assert first["start_date"] == "2026-04-01"
    assert first["end_date"] == "2026-04-05"
    assert first["total_return"] == 6.77
    assert first["eps_contribution"] == 1.89
    assert first["valuation_contribution"] == 4.88


def test_price_attribution_returns_not_found_for_missing_index(client):
    response = client.get("/api/v1/valuation/price-attribution?index=NDX&tag=month")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "no price attribution data found for index=NDX tag=month",
        }
    }
