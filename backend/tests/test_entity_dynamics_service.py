from datetime import datetime

from app.repositories.models import IntelligenceEventRow, IntelligenceSourceRow
from app.services.entity_dynamics_service import EntityDynamicsService


class FakeRepository:
    def __init__(self):
        self.last_entity_id = None

    def fetch_events(self, domain, event_tag, search, min_score=None, entity_id=None, limit=100, offset=0, since=None, before=None, favorite_only=False):
        self.last_entity_id = entity_id
        self.last_favorite_only = favorite_only
        return [
            IntelligenceEventRow(
                id=1,
                event_key="finance:microsoft:kol_opinion:rate",
                domain=domain,
                title="MSFT AI capex view",
                title_zh="",
                summary="A KOL discusses Microsoft AI capex.",
                tldr_zh="",
                first_seen_at=datetime(2026, 5, 15, 9, 30),
                last_seen_at=datetime(2026, 5, 15, 9, 30),
                entity_ids=["microsoft", "microsoft"],
                event_tags=["kol_opinion"],
                topic_tags=[],
                importance_score=70,
                status="new",
                source_count=1,
                primary_source=IntelligenceSourceRow(
                    id=1,
                    event_id=1,
                    external_id="1",
                    source_name="x_list_finance",
                    source_platform="X",
                    source_type="KOL",
                    source_url="https://x.com/example/status/1",
                    author_avatar_url="https://unavatar.io/x/example",
                    author_name="@example",
                    source_date=datetime(2026, 5, 15, 9, 30),
                    title="MSFT AI capex view",
                    summary="A KOL discusses Microsoft AI capex.",
                    raw_content="A KOL discusses Microsoft AI capex.",
                ),
            )
        ]


def test_finance_feed_passes_entity_filter_and_dedupes_entity_labels(tmp_path):
    repository = FakeRepository()
    service = EntityDynamicsService(second_brain_path=str(tmp_path), intelligence_feed_repository=repository)

    response = service.get_feed(channel="finance", filter_key="all", entity="microsoft")

    assert repository.last_entity_id == "microsoft"
    assert response.items[0].entity_labels == ["MSFT"]


def test_favorite_filter_passes_favorite_only(tmp_path):
    repository = FakeRepository()
    service = EntityDynamicsService(second_brain_path=str(tmp_path), intelligence_feed_repository=repository)

    service.get_feed(channel="ai", filter_key="favorite")

    assert repository.last_favorite_only is True


def test_favorite_feed_includes_saved_events_outside_recent_bucket(tmp_path):
    class FavoriteRepository:
        def fetch_events(self, domain, event_tag, search, min_score=None, entity_id=None, limit=100, offset=0, since=None, before=None, favorite_only=False):
            if since is not None or before is not None or not favorite_only:
                return []
            return [
                IntelligenceEventRow(
                    id=1,
                    event_key="ai:openai:product_tool_update:codex",
                    domain=domain,
                    title="OpenAI updates Codex",
                    title_zh="OpenAI 更新 Codex",
                    summary="OpenAI updates Codex.",
                    tldr_zh="OpenAI 更新 Codex。",
                    first_seen_at=datetime(2026, 5, 15, 9, 0),
                    last_seen_at=datetime(2026, 5, 15, 9, 30),
                    entity_ids=["openai"],
                    event_tags=["product_tool_update"],
                    topic_tags=[],
                    importance_score=80,
                    status="new",
                    source_count=1,
                    is_favorited=True,
                )
            ]

    service = EntityDynamicsService(second_brain_path=str(tmp_path), intelligence_feed_repository=FavoriteRepository())

    response = service.get_feed(channel="ai", filter_key="favorite")

    assert [item.slug for item in response.items] == ["event:1"]
    assert response.has_more is False


def test_event_detail_uses_source_assets_when_fetch_event_has_no_primary_source(tmp_path):
    class DetailRepository:
        def fetch_event(self, event_id):
            return IntelligenceEventRow(
                id=event_id,
                event_key="ai:openai:product_tool_update:codex",
                domain="ai",
                title="OpenAI updates Codex",
                title_zh="OpenAI 更新 Codex",
                summary="OpenAI updates Codex.",
                tldr_zh="OpenAI 更新 Codex。",
                first_seen_at=datetime(2026, 5, 15, 9, 0),
                last_seen_at=datetime(2026, 5, 15, 9, 30),
                entity_ids=["openai"],
                event_tags=["product_tool_update"],
                topic_tags=[],
                importance_score=80,
                status="new",
                source_count=1,
            )

        def fetch_sources_for_event(self, event_id):
            return [
                IntelligenceSourceRow(
                    id=1,
                    event_id=event_id,
                    external_id="source-1",
                    source_name="x_list_ai",
                    source_platform="X",
                    source_type="KOL",
                    source_url="https://x.com/openai/status/1",
                    author_avatar_url=None,
                    author_name="@openai",
                    source_date=datetime(2026, 5, 15, 9, 30),
                    title="OpenAI updates Codex",
                    summary="OpenAI updates Codex.",
                    raw_content="OpenAI updates Codex.",
                    assets=[{"type": "image", "url": "https://pbs.twimg.com/media/a.jpg?format=jpg&name=orig"}],
                )
            ]

    service = EntityDynamicsService(second_brain_path=str(tmp_path), intelligence_feed_repository=DetailRepository())

    detail = service.get_detail("event:1")

    assert detail is not None
    assert detail.assets[0]["url"] == "https://pbs.twimg.com/media/a.jpg?format=jpg&name=orig"


def test_deep_dive_feed_reads_analysis_notes_with_artifacts(tmp_path):
    analyses_dir = tmp_path / "wiki" / "analyses"
    html_dir = tmp_path / "wiki" / "html"
    analyses_dir.mkdir(parents=True)
    html_dir.mkdir(parents=True)
    html_dir.joinpath("amazon-map.html").write_text("<!doctype html><title>Amazon Map</title>", encoding="utf-8")
    analyses_dir.joinpath("20260616_manual_amazon-map.md").write_text(
        """---
type: analysis
title: Amazon 2025 Shareholder Letter Strategic Map
title_zh: 亚马逊 2025 股东信战略地图
date_created: '2026-06-16'
summary_en: Amazon frames AI capex through the AWS playbook.
summary_zh: Amazon 用 AWS 剧本解释 AI 资本开支。
artifact_html: amazon-map.html
frontend_category: deep_dive
event_tags:
  - close_reading
tags:
  - amazon
  - ai_tech
topic_tags:
  - ai_capex
---

# Amazon 2025 Shareholder Letter Strategic Map
""",
        encoding="utf-8",
    )
    service = EntityDynamicsService(second_brain_path=str(tmp_path), intelligence_feed_repository=FakeRepository())

    response = service.get_feed(channel="deep_dive", filter_key="close_reading")

    assert len(response.items) == 1
    item = response.items[0]
    assert item.slug == "deep:20260616_manual_amazon-map"
    assert item.title == "Amazon 2025 Shareholder Letter Strategic Map"
    assert item.title_zh == "亚马逊 2025 股东信战略地图"
    assert item.summary == "Amazon frames AI capex through the AWS playbook."
    assert item.tldr_zh == "Amazon 用 AWS 剧本解释 AI 资本开支。"
    assert item.source_platform == "Analysis"
    assert item.source_url is None
    assert item.entity_labels == ["Amazon - AMZN"]


def test_deep_dive_detail_returns_html_artifact_metadata(tmp_path):
    analyses_dir = tmp_path / "wiki" / "analyses"
    html_dir = tmp_path / "wiki" / "html"
    analyses_dir.mkdir(parents=True)
    html_dir.mkdir(parents=True)
    html_dir.joinpath("amazon-map.html").write_text("<!doctype html><title>Amazon Map</title>", encoding="utf-8")
    analyses_dir.joinpath("20260616_manual_amazon-map.md").write_text(
        """---
type: analysis
title: Amazon 2025 Shareholder Letter Strategic Map
summary_en: Amazon frames AI capex through the AWS playbook.
artifact_html: amazon-map.html
frontend_category: deep_dive
event_tags: [close_reading]
entity_ids: [amazon]
---

# Amazon 2025 Shareholder Letter Strategic Map
""",
        encoding="utf-8",
    )
    service = EntityDynamicsService(second_brain_path=str(tmp_path), intelligence_feed_repository=FakeRepository())

    detail = service.get_detail("deep:20260616_manual_amazon-map")

    assert detail is not None
    assert detail.artifact is not None
    assert detail.artifact.type == "html"
    assert detail.artifact.title == "Amazon 2025 Shareholder Letter Strategic Map"
    assert detail.artifact.url == "/api/v1/entity-dynamics/artifacts/html/amazon-map.html"
