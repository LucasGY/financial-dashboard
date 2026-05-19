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
              "importance_score": 84,
              "sources": [
                {
                  "source_id": "source-1",
                  "title_zh": "OpenAI 发布 Codex CLI 0.26 并改善速率限制",
                  "summary_zh": "该来源称 Codex CLI 改善了速率限制可见性。",
                  "raw_content_zh": "该版本增加了更好的速率限制跟踪。"
                },
                {
                  "source_id": "source-2",
                  "title_zh": "Codex CLI 现在显示更清晰的速率限制跟踪",
                  "summary_zh": "该来源强调新的速率限制跟踪。",
                  "raw_content_zh": "Codex CLI 现在显示更清晰的速率限制跟踪。"
                }
              ]
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
    assert event.source_translations["source-1"]["title_zh"].startswith("OpenAI 发布")
    assert event.source_translations["source-2"]["raw_content_zh"].startswith("Codex CLI")
    assert provider.response_format == {"type": "json_object"}
    assert provider.max_tokens >= 5000
    prompt = provider.messages[1].content
    assert "rule_event_tag" not in prompt
    assert '"entity_ids": []' not in prompt


def test_synthesize_events_sends_source_role_relationships_and_asset_count():
    provider = FakeProvider(
        """
        {
          "events": [
            {
              "source_ids": ["source-1"],
              "title_en": "OpenAI updates Codex",
              "title_zh": "OpenAI 更新 Codex",
              "summary_en": "OpenAI updates Codex.",
              "summary_zh": "OpenAI 更新 Codex。",
              "event_tag": "product_tool_update",
              "entity_ids": ["openai"],
              "importance_score": 80
            }
          ]
        }
        """
    )
    service = EventSynthesisService(provider)
    item = {
        **make_source_item(),
        "external_id": "source-1",
        "source_role": "related_discussion",
        "assets": [{"type": "image", "url": "https://example.test/a.jpg"}],
        "quoted_url": "https://x.com/openai/status/1",
        "reposted_url": None,
        "reply_to_url": None,
    }

    service.synthesize_events([item])

    payload = json.loads(provider.messages[1].content)
    prompt_item = payload["items"][0]
    assert prompt_item["source_role"] == "related_discussion"
    assert prompt_item["assets_count"] == 1
    assert prompt_item["quoted_url"] == "https://x.com/openai/status/1"
    assert "Primary sources define event facts" in provider.messages[0].content


def test_synthesize_events_filters_background_entities_for_arxiv_paper():
    provider = FakeProvider(
        """
        {
          "events": [
            {
              "source_ids": ["paper-1"],
              "title_en": "Two-Dimensional Framework for AI Agent Design Patterns",
              "title_zh": "AI智能体设计模式的二维框架",
              "summary_en": "A framework classifies agent design patterns across cognitive and topology axes.",
              "summary_zh": "该框架按认知和拓扑维度分类智能体设计模式。",
              "event_tag": "paper_research",
              "entity_ids": ["anthropic", "google"],
              "importance_score": 80
            }
          ]
        }
        """
    )
    service = EventSynthesisService(provider)
    item = {
        **make_source_item(),
        "external_id": "paper-1",
        "source_platform": "Paper",
        "source_type": "Researcher",
        "title": "A Two-Dimensional Framework for AI Agent Design Patterns",
        "raw_content": (
            "Existing frameworks for LLM-based agent architectures describe systems from a single perspective: "
            "industry guides (Anthropic, Google, LangChain) focus on execution topology. "
            "We propose a two-dimensional classification that combines cognitive function and execution topology."
        ),
    }

    groups = service.synthesize_events([item])

    assert len(groups) == 1
    assert groups[0][1].entity_ids == []


def test_synthesize_events_keeps_paper_entity_when_entity_is_in_title():
    provider = FakeProvider(
        """
        {
          "events": [
            {
              "source_ids": ["paper-1"],
              "title_en": "NVIDIA trains billion-parameter models without backpropagation",
              "title_zh": "NVIDIA无需反向传播训练十亿参数模型",
              "summary_en": "NVIDIA demonstrates Evolution Strategies for training large models.",
              "summary_zh": "NVIDIA展示了用进化策略训练大型模型。",
              "event_tag": "paper_research",
              "entity_ids": ["nvidia"],
              "importance_score": 80
            }
          ]
        }
        """
    )
    service = EventSynthesisService(provider)
    item = {
        **make_source_item(),
        "external_id": "paper-1",
        "source_platform": "Paper",
        "source_type": "Researcher",
        "title": "NVIDIA trains billion-parameter models without backpropagation",
        "raw_content": "The paper presents NVIDIA research on Evolution Strategies.",
    }

    groups = service.synthesize_events([item])

    assert len(groups) == 1
    assert groups[0][1].entity_ids == ["nvidia"]


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
