from app.services.event_synthesis_service import EventSynthesisService
from app.repositories.models import IntelligenceEventRow
import json
from datetime import datetime


class FakeProvider:
    def __init__(self, response: str, configured: bool = True):
        self.response = response
        self.configured = configured
        self.messages = []

    def is_configured(self):
        return self.configured

    def generate(self, messages, temperature=0.0, response_format=None, max_tokens=None):
        self.messages = messages
        self.response_format = response_format
        self.max_tokens = max_tokens
        return self.response


def make_source_item():
    return {
        "domain": "ai",
        "source_platform": "X",
        "source_type": "KOL",
        "title": "OpenAI releases Codex CLI 0.26 with better limits",
        "summary": "The release adds better rate limit tracking, OpenRouter support, and new workflow controls.",
        "raw_content": "The release adds better rate limit tracking, OpenRouter support, and new workflow controls.",
        "entity_ids": [],
        "event_tags": [],
        "importance_score": 70,
    }


def test_synthesize_event_uses_llm_json():
    provider = FakeProvider(
        """
        {
          "title_en": "OpenAI updates Codex CLI developer workflow",
          "title_zh": "OpenAI 更新 Codex CLI 开发者工作流",
          "summary_en": "Codex CLI 0.26 improves rate-limit visibility and adds OpenRouter support for agent workflows.",
          "summary_zh": "Codex CLI 0.26 改善了速率限制可见性，并为 agent 工作流加入 OpenRouter 支持。",
          "event_tag": "product_tool_update",
          "entity_ids": ["openai"],
          "importance_score": 82
        }
        """
    )
    service = EventSynthesisService(provider)

    result = service.synthesize(make_source_item())

    assert result.title == "OpenAI updates Codex CLI developer workflow"
    assert result.title_zh == "OpenAI 更新 Codex CLI 开发者工作流"
    assert result.summary.startswith("Codex CLI 0.26 improves")
    assert result.summary_zh.startswith("Codex CLI 0.26 改善")
    assert result.event_tag == "product_tool_update"
    assert result.entity_ids == ["openai"]
    assert result.importance_score == 82
    assert provider.messages[0].role == "system"
    assert provider.response_format == {"type": "json_object"}
    assert provider.max_tokens >= 2000


def test_synthesize_event_rejects_invalid_tag_and_falls_back():
    provider = FakeProvider(
        """
        {
          "title": "Bad tag",
          "summary": "Bad tag",
          "event_tag": "not_allowed",
          "importance_score": 99
        }
        """
    )
    service = EventSynthesisService(provider)

    result = service.synthesize(make_source_item())

    assert result.title == "OpenAI releases Codex CLI 0.26 with better limits"
    assert result.event_tag == "industry"
    assert result.importance_score == 70


def test_synthesize_event_falls_back_when_provider_unconfigured():
    provider = FakeProvider("{}", configured=False)
    service = EventSynthesisService(provider)

    result = service.synthesize(make_source_item())

    assert result.title == "OpenAI releases Codex CLI 0.26 with better limits"
    assert result.summary.startswith("The release adds")
    assert result.event_tag == "industry"


def test_synthesize_events_rejects_missing_llm_score():
    provider = FakeProvider(
        """
        {
          "events": [
            {
              "source_ids": ["source-1"],
              "title_en": "OpenAI updates Codex",
              "title_zh": "OpenAI 更新 Codex",
              "summary_en": "OpenAI updates Codex.",
              "summary_zh": "OpenAI 更新了 Codex。",
              "event_tag": "product_tool_update",
              "entity_ids": ["openai"]
            }
          ]
        }
        """
    )
    service = EventSynthesisService(provider)
    item = {**make_source_item(), "external_id": "source-1", "importance_score": 99}

    groups = service.synthesize_events([item])

    assert groups == []
    prompt_payload = json.loads(provider.messages[1].content)
    assert "importance_score" not in prompt_payload["items"][0]


def test_synthesize_events_uses_llm_entities_and_does_not_send_rule_labels():
    provider = FakeProvider(
        """
        {
          "events": [
            {
              "source_ids": ["source-1", "source-2"],
              "title_en": "OpenAI updates Codex CLI rate-limit workflow",
              "title_zh": "OpenAI 更新 Codex CLI 速率限制工作流",
              "summary_en": "Two sources describe a Codex CLI update focused on rate-limit visibility.",
              "summary_zh": "两条来源显示，Codex CLI 更新重点改善了速率限制可见性。",
              "event_tag": "product_tool_update",
              "entity_ids": ["openai"],
              "importance_score": 84
            }
          ]
        }
        """
    )
    service = EventSynthesisService(provider)
    first = {**make_source_item(), "external_id": "source-1"}
    second = {**make_source_item(), "external_id": "source-2", "title": "Codex CLI now shows clearer rate limit tracking"}

    groups = service.synthesize_events([first, second])

    assert len(groups) == 1
    sources, event = groups[0]
    assert [source["external_id"] for source in sources] == ["source-1", "source-2"]
    assert event.title == "OpenAI updates Codex CLI rate-limit workflow"
    assert event.title_zh == "OpenAI 更新 Codex CLI 速率限制工作流"
    assert event.summary == "Two sources describe a Codex CLI update focused on rate-limit visibility."
    assert event.summary_zh == "两条来源显示，Codex CLI 更新重点改善了速率限制可见性。"
    assert event.entity_ids == ["openai"]
    assert event.event_tag == "product_tool_update"
    assert provider.response_format == {"type": "json_object"}
    assert provider.max_tokens >= 5000
    prompt = provider.messages[1].content
    assert "rule_event_tag" not in prompt
    assert '"entity_ids": []' not in prompt


def test_match_existing_event_uses_llm_merge_decision():
    provider = FakeProvider(
        """
        {
          "decision": "merge",
          "target_event_key": "ai:openai:product_tool_update:codex-cli",
          "reason": "same Codex CLI release"
        }
        """
    )
    service = EventSynthesisService(provider)
    existing = IntelligenceEventRow(
        id=1,
        event_key="ai:openai:product_tool_update:codex-cli",
        domain="ai",
        title="OpenAI updates Codex CLI",
        title_zh="OpenAI 更新 Codex CLI",
        summary="OpenAI updates Codex CLI.",
        tldr_zh="OpenAI 更新 Codex CLI。",
        first_seen_at=datetime(2026, 5, 15, 9, 0),
        last_seen_at=datetime(2026, 5, 15, 9, 30),
        entity_ids=["openai"],
        event_tags=["product_tool_update"],
        topic_tags=[],
        importance_score=82,
        status="new",
        source_count=1,
    )

    target = service.match_existing_event(
        {
            "title": "Codex CLI gets clearer limits",
            "title_zh": "Codex CLI 改善限制提示",
            "summary": "Another source describes the same Codex CLI release.",
            "tldr_zh": "另一个来源描述同一 Codex CLI 发布。",
            "event_tags": ["product_tool_update"],
            "entity_ids": ["openai"],
            "last_seen_at": datetime(2026, 5, 15, 10, 0),
        },
        [existing],
    )

    assert target == "ai:openai:product_tool_update:codex-cli"
    assert provider.response_format == {"type": "json_object"}
    payload = json.loads(provider.messages[1].content)
    assert payload["existing_events"][0]["event_key"] == "ai:openai:product_tool_update:codex-cli"


def test_match_existing_event_rejects_unknown_target_key():
    provider = FakeProvider(
        """
        {
          "decision": "merge",
          "target_event_key": "unknown",
          "reason": "bad target"
        }
        """
    )
    service = EventSynthesisService(provider)
    existing = IntelligenceEventRow(
        id=1,
        event_key="ai:openai:product_tool_update:codex-cli",
        domain="ai",
        title="OpenAI updates Codex CLI",
        title_zh="OpenAI 更新 Codex CLI",
        summary="OpenAI updates Codex CLI.",
        tldr_zh="OpenAI 更新 Codex CLI。",
        first_seen_at=datetime(2026, 5, 15, 9, 0),
        last_seen_at=datetime(2026, 5, 15, 9, 30),
        entity_ids=["openai"],
        event_tags=["product_tool_update"],
        topic_tags=[],
        importance_score=82,
        status="new",
        source_count=1,
    )

    assert service.match_existing_event({}, [existing]) is None
