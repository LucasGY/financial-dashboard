from app.services.sandbox_service import SandboxService


def test_strategy_lab_run_success_and_result(client):
    response = client.post(
        "/api/v1/strategy-lab/runs",
        json={
            "prompt": "当恐贪指数小于20且VIX大于25时，买入SPY，持有5、20、60个交易日",
            "target_ticker": "SPY",
            "start_date": "2026-04-01",
            "end_date": "2026-04-04",
            "forward_windows": [2, 3],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"

    result_response = client.get(f"/api/v1/strategy-lab/runs/{payload['run_id']}/result")
    assert result_response.status_code == 200
    result = result_response.json()
    assert result["strategy_spec"]["target_ticker"] == "SPY"
    assert result["summary_metrics"][0]["window_days"] == 2
    assert "def build_signal" in result["generated_code"]
    assert result["charts"]["price_series"]


def test_strategy_lab_supports_cnn_vix_and_ntm_pe_conditions(client):
    response = client.post(
        "/api/v1/strategy-lab/runs",
        json={
            "prompt": "当 CNN Fear & Greed 小于20 且 VIX 大于25 且 标普 NTM PE 小于17 时，买入SPY，持有2个交易日",
            "target_ticker": "SPY",
            "start_date": "2026-04-01",
            "end_date": "2026-04-04",
            "forward_windows": [2],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"

    result_response = client.get(f"/api/v1/strategy-lab/runs/{payload['run_id']}/result")
    assert result_response.status_code == 200
    result = result_response.json()
    indicators = [item["indicator"] for item in result["strategy_spec"]["entry_conditions"]]
    assert "cnn_fear_greed" in indicators
    assert "vix" in indicators
    assert "ntm_pe" in indicators


def test_strategy_lab_prompt_target_overrides_request_target(client):
    response = client.post(
        "/api/v1/strategy-lab/runs",
        json={
            "prompt": "当 CNN Fear & Greed 小于20 且 VIX 大于30 且 纳指 NTM PE 小于25 时，买入 QQQ，持有 90 天",
            "target_ticker": "SPY",
            "start_date": "2026-04-01",
            "end_date": "2026-04-04",
            "forward_windows": [2],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"

    result_response = client.get(f"/api/v1/strategy-lab/runs/{payload['run_id']}/result")
    assert result_response.status_code == 200
    result = result_response.json()
    assert result["strategy_spec"]["target_ticker"] == "QQQ"
    assert any("SPY -> QQQ" in item for item in result["strategy_spec"]["parse_notes"])


def test_strategy_lab_returns_failed_status_for_unsupported_prompt(client):
    response = client.post(
        "/api/v1/strategy-lab/runs",
        json={
            "prompt": "请给我做一个多资产再平衡组合，带止盈止损和仓位控制",
            "target_ticker": "SPY",
            "start_date": "2026-04-01",
            "end_date": "2026-04-04",
            "forward_windows": [5],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"


def test_strategy_lab_validation_error_for_bad_ticker(client):
    response = client.post(
        "/api/v1/strategy-lab/runs",
        json={
            "prompt": "当恐贪指数小于20时买入",
            "target_ticker": "TSM",
            "start_date": "2026-04-01",
            "end_date": "2026-04-04",
            "forward_windows": [5],
        },
    )

    assert response.status_code == 400
    assert "target_ticker" in response.json()["error"]["message"]


def test_sandbox_blocks_imports():
    service = SandboxService()
    code = "def build_signal(context):\n    import os\n    return True\n"

    try:
        service.validate_code(code)
        assert False, "expected validate_code to fail"
    except Exception as exc:  # noqa: BLE001
        assert "blocked" in str(exc)
