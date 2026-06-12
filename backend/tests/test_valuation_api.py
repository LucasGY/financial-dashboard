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


def test_drawdown_scenarios_contract(client):
    response = client.get("/api/v1/valuation/drawdown-scenarios")

    assert response.status_code == 200
    payload = response.json()
    spy = payload["spy"]
    current_row = next(item for item in spy["scenarios"] if item["is_current_drawdown_row"])
    key_rows = {item["drawdown_pct"] for item in spy["scenarios"] if item["is_key_drawdown"]}
    cheap_rows = [item for item in spy["scenarios"] if item["is_cheap"]]

    assert spy["ticker"] == "SPY"
    assert spy["index_code"] == "SPX"
    assert spy["current_price"] == 108.64
    assert spy["high_price"] == 112.0
    assert spy["current_drawdown_pct"] == -3.0
    assert current_row["drawdown_pct"] == -3.0
    assert current_row["price_level"] == 108.64
    assert current_row["implied_pe"] == 22.4
    assert current_row["percentile_1y"] == 100.0
    assert [item["drawdown_pct"] for item in spy["scenarios"][1:4]] == [-2, -3.0, -4]
    assert key_rows == {-5, -10, -15}
    assert cheap_rows[-1]["drawdown_pct"] == -30
    assert cheap_rows[-1]["percentile_5y"] < 20
    assert payload["qqq"] is None
