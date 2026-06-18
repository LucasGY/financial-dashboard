from app.api.dependencies import get_entity_dynamics_service
from app.schemas.entity_dynamics import FeedResponse, IntelligenceArtifact, IntelligenceItem, IntelligenceSource, SourceDetail


class FakeEntityDynamicsService:
    def __init__(self):
        self.last_min_score = None
        self.last_entity = None
        self.last_favorite = None
        self.artifact_path = None

    def get_feed(self, channel="ai", filter_key="all", search=None, min_score=None, entity=None, limit=35, cursor=None):
        self.last_min_score = min_score
        self.last_entity = entity
        return FeedResponse(
            items=[
                IntelligenceItem(
                    id="event:1",
                    slug="event:1",
                    channel=channel,
                    domain="ai",
                    source_kind="feed",
                    source_platform="X",
                    source_type="KOL",
                    source_role="primary",
                    source_name="x_list_ai",
                    author_name="@example",
                    source_date="2026-05-15 09:30",
                    title="OpenAI ships a Codex update",
                    title_zh="OpenAI 发布 Codex 更新",
                    summary="Codex can be controlled from mobile ChatGPT.",
                    tldr_zh="Codex 支持通过 ChatGPT 手机端远程控制。",
                    tldr_en="Codex can be controlled from mobile ChatGPT.",
                    assets=[{"type": "image", "url": "https://example.test/card.jpg"}],
                    entity_ids=["openai"],
                    entity_labels=["OpenAI"],
                    event_tags=["product_tool_update"],
                    topic_tags=["codex"],
                    importance_score=72,
                    source_count=2,
                    has_related_discussions=True,
                    is_favorited=False,
                    source_url="https://x.com/example/status/1",
                    author_avatar_url="https://unavatar.io/x/example",
                    status="new",
                )
            ]
        )

    def get_detail(self, slug):
        return SourceDetail(
            id=slug,
            slug=slug,
            channel="ai",
            domain="ai",
            source_kind="feed",
            source_platform="X",
            source_type="KOL",
            source_name="x_list_ai",
            author_name="@example",
            source_date="2026-05-15 09:30",
            title="OpenAI ships a Codex update",
            title_zh="OpenAI 发布 Codex 更新",
            summary="Codex can be controlled from mobile ChatGPT.",
            tldr_zh="Codex 支持通过 ChatGPT 手机端远程控制。",
            tldr_en="Codex can be controlled from mobile ChatGPT.",
            entity_ids=["openai"],
            entity_labels=["OpenAI"],
            event_tags=["product_tool_update"],
            topic_tags=["codex"],
            importance_score=72,
            source_count=2,
            source_url="https://x.com/example/status/1",
            author_avatar_url="https://unavatar.io/x/example",
            status="new",
            content="Raw source text",
            artifact=IntelligenceArtifact(type="html", title="Artifact", url="/api/v1/entity-dynamics/artifacts/html/artifact.html"),
            sources=[
                IntelligenceSource(
                    id="source:1",
                    source_name="x_list_ai",
                    source_platform="X",
                    source_type="KOL",
                    source_role="related_discussion",
                    original_url="https://x.com/example/status/1",
                    quoted_url="https://x.com/openai/status/1",
                    reposted_url=None,
                    reply_to_url=None,
                    assets=[{"type": "image", "url": "https://example.test/a.jpg"}],
                    extraction_status="extracted",
                    author_name="@example",
                    source_date="2026-05-15 09:30",
                    title="OpenAI ships a Codex update",
                    title_zh="OpenAI 发布 Codex 更新",
                    summary="Codex can be controlled from mobile ChatGPT.",
                    summary_zh="Codex 支持通过 ChatGPT 手机端远程控制。",
                    source_url="https://x.com/example/status/1",
                    author_avatar_url="https://unavatar.io/x/example",
                    raw_content="Raw source text",
                    raw_content_zh="原始来源文本",
                )
            ],
        )

    def set_favorite(self, slug, is_favorited):
        self.last_favorite = (slug, is_favorited)
        return {"slug": slug, "is_favorited": is_favorited}

    def resolve_html_artifact(self, filename):
        if filename == "artifact.html":
            return self.artifact_path
        return None


def test_entity_dynamics_feed_contract(client):
    fake_service = FakeEntityDynamicsService()
    client.app.dependency_overrides[get_entity_dynamics_service] = lambda: fake_service

    response = client.get("/api/v1/entity-dynamics/feed?channel=finance&filter=all&entity=microsoft&min_score=60")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["id"] == "event:1"
    assert payload["items"][0]["source_kind"] == "feed"
    assert payload["items"][0]["source_count"] == 2
    assert payload["items"][0]["has_related_discussions"] is True
    assert payload["items"][0]["assets"][0]["url"] == "https://example.test/card.jpg"
    assert payload["items"][0]["entity_ids"] == ["openai"]
    assert fake_service.last_min_score == 60
    assert fake_service.last_entity == "microsoft"


def test_entity_dynamics_detail_contract(client):
    client.app.dependency_overrides[get_entity_dynamics_service] = lambda: FakeEntityDynamicsService()

    response = client.get("/api/v1/entity-dynamics/sources/event%3A1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "event:1"
    assert payload["content"] == "Raw source text"
    assert payload["artifact"]["url"] == "/api/v1/entity-dynamics/artifacts/html/artifact.html"
    assert len(payload["sources"]) == 1
    assert payload["sources"][0]["source_role"] == "related_discussion"
    assert payload["sources"][0]["assets"][0]["url"] == "https://example.test/a.jpg"
    assert payload["sources"][0]["title_zh"] == "OpenAI 发布 Codex 更新"
    assert payload["sources"][0]["raw_content_zh"] == "原始来源文本"


def test_entity_dynamics_favorite_contract(client):
    fake_service = FakeEntityDynamicsService()
    client.app.dependency_overrides[get_entity_dynamics_service] = lambda: fake_service

    response = client.post("/api/v1/entity-dynamics/sources/event%3A1/favorite", json={"is_favorited": True})

    assert response.status_code == 200
    assert response.json() == {"slug": "event:1", "is_favorited": True}
    assert fake_service.last_favorite == ("event:1", True)


def test_entity_dynamics_html_artifact_contract(client, tmp_path):
    artifact_path = tmp_path / "artifact.html"
    artifact_path.write_text("<!doctype html><title>Artifact</title>", encoding="utf-8")
    fake_service = FakeEntityDynamicsService()
    fake_service.artifact_path = artifact_path
    client.app.dependency_overrides[get_entity_dynamics_service] = lambda: fake_service

    response = client.get("/api/v1/entity-dynamics/artifacts/html/artifact.html")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Artifact" in response.text


def test_entity_dynamics_html_artifact_returns_404_for_unknown_file(client):
    client.app.dependency_overrides[get_entity_dynamics_service] = lambda: FakeEntityDynamicsService()

    response = client.get("/api/v1/entity-dynamics/artifacts/html/missing.html")

    assert response.status_code == 404
