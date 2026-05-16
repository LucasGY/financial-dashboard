from app.services.intelligence_taxonomy import entity_labels_for_channel


def test_normalize_event_tags_removes_market_for_finance():
    from app.services.intelligence_taxonomy import normalize_event_tags_for_domain

    assert normalize_event_tags_for_domain("finance", ["market"]) == ["kol_opinion"]
    assert normalize_event_tags_for_domain("finance", ["market", "macro"]) == ["macro"]


def test_entity_labels_are_channel_specific():
    assert entity_labels_for_channel(["microsoft", "openai"], "ai") == ["Microsoft", "OpenAI"]
    assert entity_labels_for_channel(["microsoft", "nvidia"], "finance") == ["MSFT", "NVDA"]
    assert entity_labels_for_channel(["microsoft"], "deep_dive") == ["Microsoft - MSFT"]
