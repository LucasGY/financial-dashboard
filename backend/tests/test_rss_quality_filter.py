from app.services.rss_quality_filter import evaluate_rss_item


def test_quality_filter_accepts_high_signal_ai_update():
    decision = evaluate_rss_item(
        domain="ai",
        source_platform="X",
        source_type="KOL",
        title="OpenAI releases Codex CLI 0.26",
        summary="The update adds better rate limit tracking, OpenRouter support, and new agent workflow controls.",
        entity_ids=["openai"],
        event_tags=["product_tool_update"],
        source_url="https://x.com/example/status/1",
    )

    assert decision.should_ingest is True
    assert decision.score == 0
    assert decision.reason == "accepted"


def test_quality_filter_rejects_low_signal_reaction():
    decision = evaluate_rss_item(
        domain="ai",
        source_platform="X",
        source_type="KOL",
        title="Re @someone lol",
        summary="Re @someone lol",
        entity_ids=[],
        event_tags=["industry"],
        source_url="https://x.com/example/status/2",
    )

    assert decision.should_ingest is False
    assert decision.score == 0
    assert decision.reason == "low_signal"


def test_quality_filter_hard_rejects_promotional_content():
    decision = evaluate_rss_item(
        domain="ai",
        source_platform="X",
        source_type="KOL",
        title="Join my course and use discount code AI50",
        summary="Subscribe now for a limited discount code and course bundle.",
        entity_ids=[],
        event_tags=["industry"],
        source_url="https://x.com/example/status/3",
    )

    assert decision.should_ingest is False
    assert decision.reason == "promotional"
