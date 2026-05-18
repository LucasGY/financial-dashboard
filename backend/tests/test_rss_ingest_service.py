from app.services.rss_ingest_service import RssIngestService, build_event_key, normalize_entry
from app.services.rss_source_config import RssSource
from app.repositories.models import IntelligenceEventRow
from datetime import datetime


def test_normalize_entry_classifies_and_preserves_x_rss_content():
    source = RssSource(
        domain="ai",
        name="x_list_ai",
        url="http://49.51.253.23:1200/twitter/list/2010668465980424307",
        platform="X",
    )
    entry = {
        "id": "https://x.com/example/status/1",
        "link": "https://x.com/example/status/1",
        "title": "OpenAI releases new Codex tool",
        "summary": "Codex now supports mobile control from ChatGPT.",
        "author": "@example",
        "published": "Fri, 15 May 2026 09:30:00 GMT",
    }

    item = normalize_entry(source, entry)

    assert item["external_id"] == "https://x.com/example/status/1"
    assert item["domain"] == "ai"
    assert item["source_platform"] == "X"
    assert item["entity_ids"] == []
    assert item["event_tags"] == []
    assert item["raw_content"] == "Codex now supports mobile control from ChatGPT."
    assert item["importance_score"] is None
    assert "rule_score" not in item
    assert item["author_avatar_url"] == "https://unavatar.io/x/example"
    assert item["source_role"] == "primary"
    assert item["assets"] == []
    assert item["extraction_status"] == "extracted"


def test_normalize_entry_extracts_x_assets_and_quote_relationship():
    source = RssSource(
        domain="ai",
        name="x_list_ai",
        url="http://49.51.253.23:1200/twitter/list/2010668465980424307",
        platform="X",
    )
    entry = {
        "id": "https://x.com/commenter/status/2",
        "link": "https://x.com/commenter/status/2",
        "title": "Interesting Codex update",
        "summary": "Interesting Codex update https://x.com/openai/status/1 <img src=\"https://pbs.twimg.com/media/a.jpg\" />",
        "author": "@commenter",
        "published": "Fri, 15 May 2026 09:30:00 GMT",
        "media_content": [{"url": "https://pbs.twimg.com/media/b.png", "type": "image/png"}],
    }

    item = normalize_entry(source, entry)

    assert item["source_role"] == "related_discussion"
    assert item["quoted_url"] == "https://x.com/openai/status/1"
    assert item["reposted_url"] is None
    assert item["reply_to_url"] is None
    assert {"type": "image", "url": "https://pbs.twimg.com/media/a.jpg"} in item["assets"]
    assert {"type": "image", "url": "https://pbs.twimg.com/media/b.png"} in item["assets"]


def test_normalize_entry_unescapes_x_asset_urls():
    source = RssSource(domain="ai", name="x_list_ai", url="http://example.test/rss", platform="X")
    entry = {
        "id": "https://x.com/example/status/5",
        "link": "https://x.com/example/status/5",
        "title": "Image post",
        "summary": "<img src=\"https://pbs.twimg.com/media/a.jpg?format=jpg&amp;name=orig\" />",
        "published": "Fri, 15 May 2026 09:30:00 GMT",
    }

    item = normalize_entry(source, entry)

    assert item["assets"][0]["url"] == "https://pbs.twimg.com/media/a.jpg?format=jpg&name=orig"


def test_normalize_entry_strips_rss_html():
    source = RssSource(domain="ai", name="x_list_ai", url="http://example.test/rss", platform="X")
    entry = {
        "id": "https://x.com/example/status/2",
        "link": "https://x.com/example/status/2",
        "title": "CodexBar 0.26.0 is live",
        "summary": "CodexBar 0.26.0 is live<br /><br />better limits<img src=\"https://example.test/a.jpg\" />",
        "published": "Fri, 15 May 2026 09:30:00 GMT",
    }

    item = normalize_entry(source, entry)

    assert item["summary"] == "better limits"
    assert "<br" not in item["raw_content"]
    assert "<img" not in item["raw_content"]


def test_normalize_entry_uses_clean_x_title_and_non_duplicate_summary():
    source = RssSource(domain="ai", name="x_list_ai", url="http://example.test/rss", platform="X")
    entry = {
        "id": "https://x.com/example/status/3",
        "link": "https://x.com/example/status/3",
        "title": "CodexBar 0.26.0 is live<br />CodexBar 0.26.0 is live",
        "summary": "CodexBar 0.26.0 is live<br />CodexBar 0.26.0 is live",
        "published": "Fri, 15 May 2026 09:30:00 GMT",
    }

    item = normalize_entry(source, entry)

    assert item["title"] == "CodexBar 0.26.0 is live"
    assert item["summary"] == ""


def test_normalize_entry_removes_title_prefix_from_summary():
    source = RssSource(domain="ai", name="x_list_ai", url="http://example.test/rss", platform="X")
    entry = {
        "id": "https://x.com/example/status/4",
        "link": "https://x.com/example/status/4",
        "title": "CodexBar 0.26.0 is live",
        "summary": "CodexBar 0.26.0 is live better limits and cost scoping",
        "published": "Fri, 15 May 2026 09:30:00 GMT",
    }

    item = normalize_entry(source, entry)

    assert item["title"] == "CodexBar 0.26.0 is live"
    assert item["summary"] == "better limits and cost scoping"


def test_build_event_key_dedupes_similar_sources():
    first = build_event_key(
        domain="ai",
        entity_ids=["openai"],
        event_tags=["product_tool_update"],
        title="OpenAI releases new Codex tool",
    )
    second = build_event_key(
        domain="ai",
        entity_ids=["openai"],
        event_tags=["product_tool_update"],
        title="OpenAI releases Codex tool update",
    )

    assert first == second


def test_ingest_sources_respects_limit_per_source(monkeypatch):
    class FakeRepository:
        def __init__(self):
            self.items = []

        def upsert_event_with_source(self, event, source):
            self.items.append((event, source))

    class FakeFeed:
        entries = [
            {"id": "1", "title": "OpenAI Codex update", "summary": "Codex update", "published": "Fri, 15 May 2026 09:30:00 GMT"},
            {"id": "2", "title": "OpenAI Codex update", "summary": "Codex update", "published": "Fri, 15 May 2026 09:31:00 GMT"},
        ]

    def fake_parse(url):
        return FakeFeed()

    import feedparser

    monkeypatch.setattr(feedparser, "parse", fake_parse)
    repository = FakeRepository()
    service = RssIngestService(repository)

    count = service.ingest_sources(
        [RssSource(domain="ai", name="x_list_ai", url="http://example.test/rss", platform="X")],
        limit_per_source=1,
    )

    assert count == 1
    assert len(repository.items) == 1


def test_ingest_sources_skips_low_quality_items(monkeypatch):
    class FakeRepository:
        def __init__(self):
            self.items = []

        def upsert_event_with_source(self, event, source):
            self.items.append((event, source))

    class FakeFeed:
        entries = [
            {"id": "1", "title": "Re @someone lol", "summary": "Re @someone lol", "published": "Fri, 15 May 2026 09:30:00 GMT"},
            {
                "id": "2",
                "title": "OpenAI releases Codex CLI 0.26",
                "summary": "The release adds better rate limit tracking and OpenRouter support.",
                "published": "Fri, 15 May 2026 09:31:00 GMT",
            },
        ]

    def fake_parse(url):
        return FakeFeed()

    import feedparser

    monkeypatch.setattr(feedparser, "parse", fake_parse)
    repository = FakeRepository()
    service = RssIngestService(repository)

    count = service.ingest_sources(
        [RssSource(domain="ai", name="x_list_ai", url="http://example.test/rss", platform="X")],
    )

    assert count == 1
    assert len(repository.items) == 1
    assert repository.items[0][1]["external_id"] == "2"


def test_ingest_sources_applies_event_synthesis(monkeypatch):
    class FakeRepository:
        def __init__(self):
            self.items = []

        def upsert_event_with_source(self, event, source):
            self.items.append((event, source))

    class FakeSynthesizer:
        def synthesize(self, source_item):
            return type(
                "SyntheticEvent",
                (),
                        {
                            "title": "OpenAI updates Codex CLI developer workflow",
                            "title_zh": "OpenAI 更新 Codex CLI 开发者工作流",
                            "summary": "Codex CLI 0.26 improves rate-limit visibility.",
                            "summary_zh": "Codex CLI 0.26 改善了速率限制可见性。",
                            "event_tag": "product_tool_update",
                            "entity_ids": ["openai"],
                            "importance_score": 82,
                        },
            )()

    class FakeFeed:
        entries = [
            {
                "id": "1",
                "title": "OpenAI releases Codex CLI 0.26",
                "summary": "The release adds better rate limit tracking and OpenRouter support.",
                "published": "Fri, 15 May 2026 09:31:00 GMT",
            },
        ]

    def fake_parse(url):
        return FakeFeed()

    import feedparser

    monkeypatch.setattr(feedparser, "parse", fake_parse)
    repository = FakeRepository()
    service = RssIngestService(repository, event_synthesizer=FakeSynthesizer())

    count = service.ingest_sources(
        [RssSource(domain="ai", name="x_list_ai", url="http://example.test/rss", platform="X")],
    )

    assert count == 1
    event, source = repository.items[0]
    assert event["title"] == "OpenAI updates Codex CLI developer workflow"
    assert event["title_zh"] == "OpenAI 更新 Codex CLI 开发者工作流"
    assert event["summary"] == "Codex CLI 0.26 improves rate-limit visibility."
    assert event["tldr_zh"] == "Codex CLI 0.26 改善了速率限制可见性。"
    assert event["event_tags"] == ["product_tool_update"]
    assert event["entity_ids"] == ["openai"]
    assert event["importance_score"] == 82
    assert source["title"] == "OpenAI releases Codex CLI 0.26"


def test_ingest_sources_uses_llm_batch_merge_before_upsert(monkeypatch):
    class FakeRepository:
        def __init__(self):
            self.items = []

        def upsert_event_with_source(self, event, source):
            self.items.append((event, source))

    class FakeSynthesizer:
        def synthesize_events(self, source_items):
            assert len(source_items) == 2
            return [
                (
                    source_items,
                    type(
                        "SyntheticEvent",
                        (),
                        {
                            "title": "OpenAI updates Codex CLI rate-limit workflow",
                            "title_zh": "OpenAI 更新 Codex CLI 速率限制工作流",
                            "summary": "Two sources describe a Codex CLI update focused on rate-limit visibility.",
                            "summary_zh": "两条来源显示，Codex CLI 更新重点改善了速率限制可见性。",
                            "event_tag": "product_tool_update",
                            "entity_ids": ["openai"],
                            "importance_score": 84,
                        },
                    )(),
                )
            ]

    class FakeFeed:
        entries = [
            {
                "id": "1",
                "title": "OpenAI releases Codex CLI 0.26 with better rate limits",
                "summary": "OpenAI releases Codex CLI 0.26 with better rate limits",
                "published": "Fri, 15 May 2026 09:31:00 GMT",
            },
            {
                "id": "2",
                "title": "Codex CLI now shows clearer rate limit tracking",
                "summary": "Codex CLI now shows clearer rate limit tracking",
                "published": "Fri, 15 May 2026 09:35:00 GMT",
            },
        ]

    def fake_parse(url):
        return FakeFeed()

    import feedparser

    monkeypatch.setattr(feedparser, "parse", fake_parse)
    repository = FakeRepository()
    service = RssIngestService(repository, event_synthesizer=FakeSynthesizer())

    count = service.ingest_sources(
        [RssSource(domain="ai", name="x_list_ai", url="http://example.test/rss", platform="X")],
    )

    assert count == 2
    assert len(repository.items) == 2
    first_event, first_source = repository.items[0]
    second_event, second_source = repository.items[1]
    assert first_event["event_key"] == second_event["event_key"]
    assert first_event["title"] == "OpenAI updates Codex CLI rate-limit workflow"
    assert first_event["title_zh"] == "OpenAI 更新 Codex CLI 速率限制工作流"
    assert first_event["summary"] == "Two sources describe a Codex CLI update focused on rate-limit visibility."
    assert first_event["tldr_zh"] == "两条来源显示，Codex CLI 更新重点改善了速率限制可见性。"
    assert first_event["event_tags"] == ["product_tool_update"]
    assert first_event["entity_ids"] == ["openai"]
    assert first_source["external_id"] == "1"
    assert second_source["external_id"] == "2"


def test_ingest_sources_skips_existing_external_ids_before_llm(monkeypatch):
    class FakeRepository:
        def __init__(self):
            self.items = []

        def fetch_existing_source_external_ids(self, external_ids):
            assert set(external_ids) == {"1", "2"}
            return {"1"}

        def upsert_event_with_source(self, event, source):
            self.items.append((event, source))

    class FakeSynthesizer:
        def synthesize_events(self, source_items):
            assert [item["external_id"] for item in source_items] == ["2"]
            return [
                (
                    source_items,
                    type(
                        "SyntheticEvent",
                        (),
                        {
                            "title": "OpenAI updates Codex CLI",
                            "title_zh": "OpenAI 更新 Codex CLI",
                            "summary": "OpenAI updates Codex CLI.",
                            "summary_zh": "OpenAI 更新了 Codex CLI。",
                            "event_tag": "product_tool_update",
                            "entity_ids": ["openai"],
                            "importance_score": 80,
                        },
                    )(),
                )
            ]

    class FakeFeed:
        entries = [
            {
                "id": "1",
                "title": "OpenAI releases Codex CLI 0.26",
                "summary": "The release adds better rate limit tracking.",
                "published": "Fri, 15 May 2026 09:30:00 GMT",
            },
            {
                "id": "2",
                "title": "OpenAI releases Codex CLI 0.27",
                "summary": "The release adds better workflow controls.",
                "published": "Fri, 15 May 2026 09:31:00 GMT",
            },
        ]

    def fake_parse(url):
        return FakeFeed()

    import feedparser

    monkeypatch.setattr(feedparser, "parse", fake_parse)
    repository = FakeRepository()
    service = RssIngestService(repository, event_synthesizer=FakeSynthesizer())

    count = service.ingest_sources(
        [RssSource(domain="ai", name="x_list_ai", url="http://example.test/rss", platform="X")],
    )

    assert count == 1
    assert len(repository.items) == 1
    assert repository.items[0][1]["external_id"] == "2"


def test_ingest_sources_sends_valid_weak_signal_items_to_llm(monkeypatch):
    class FakeRepository:
        def __init__(self):
            self.items = []

        def upsert_event_with_source(self, event, source):
            self.items.append((event, source))

    class FakeSynthesizer:
        def synthesize_events(self, source_items):
            assert [item["external_id"] for item in source_items] == ["weak-1"]
            return [
                (
                    source_items,
                    type(
                        "SyntheticEvent",
                        (),
                        {
                            "title": "Agent workflow note",
                            "title_zh": "Agent 工作流观察",
                            "summary": "A short but valid note about agent handoff review.",
                            "summary_zh": "一条简短但有效的 Agent 交接观察。",
                            "event_tag": "tips_opinion",
                            "entity_ids": ["agents"],
                            "importance_score": 61,
                        },
                    )(),
                )
            ]

    class FakeFeed:
        entries = [
            {
                "id": "weak-1",
                "title": "Agent handoff note",
                "summary": "Teams should review handoff patterns.",
                "published": "Fri, 15 May 2026 09:31:00 GMT",
            },
        ]

    def fake_parse(url):
        return FakeFeed()

    import feedparser

    monkeypatch.setattr(feedparser, "parse", fake_parse)
    repository = FakeRepository()
    service = RssIngestService(repository, event_synthesizer=FakeSynthesizer())

    count = service.ingest_sources(
        [RssSource(domain="ai", name="misc_ai", url="http://example.test/rss", platform="RSS")],
    )

    assert count == 1
    assert len(repository.items) == 1
    assert repository.items[0][1]["quality_reason"] == "accepted"


def test_ingest_sources_merges_cross_batch_event_within_48_hours(monkeypatch):
    class FakeRepository:
        def __init__(self):
            self.items = []
            self.events_by_key = {}
            self.merge_queries = []

        def fetch_recent_merge_candidates(self, *, domain, event_tag, entity_ids, since, limit=12):
            self.merge_queries.append((domain, event_tag, entity_ids, since))
            return [
                event
                for event in self.events_by_key.values()
                if event.domain == domain
                and event_tag in event.event_tags
                and set(entity_ids).intersection(event.entity_ids)
                and event.last_seen_at >= since
            ]

        def upsert_event_with_source(self, event, source):
            existing = self.events_by_key.get(event["event_key"])
            if existing:
                last_seen_at = max(existing.last_seen_at, event["last_seen_at"])
                first_seen_at = min(existing.first_seen_at, event["first_seen_at"])
                source_count = existing.source_count + 1
            else:
                first_seen_at = event["first_seen_at"]
                last_seen_at = event["last_seen_at"]
                source_count = 1
            self.events_by_key[event["event_key"]] = IntelligenceEventRow(
                id=len(self.events_by_key) + 1,
                event_key=event["event_key"],
                domain=event["domain"],
                title=event["title"],
                title_zh=event["title_zh"],
                summary=event["summary"],
                tldr_zh=event["tldr_zh"],
                first_seen_at=first_seen_at,
                last_seen_at=last_seen_at,
                entity_ids=event["entity_ids"],
                event_tags=event["event_tags"],
                topic_tags=event["topic_tags"],
                importance_score=event["importance_score"],
                status=event["status"],
                source_count=source_count,
            )
            self.items.append((event, source))

    class FakeSynthesizer:
        def __init__(self):
            self.merge_candidates = []

        def synthesize_events(self, source_items):
            first_source = source_items[0]
            if first_source["external_id"] == "6":
                title = "Codex CLI rate limit workflow gets another mention"
                title_zh = "Codex CLI 速率限制工作流再次被提及"
            else:
                title = "OpenAI updates Codex CLI rate-limit workflow"
                title_zh = "OpenAI 更新 Codex CLI 速率限制工作流"
            return [
                (
                    source_items,
                    type(
                        "SyntheticEvent",
                        (),
                        {
                            "title": title,
                            "title_zh": title_zh,
                            "summary": "Sources describe the same Codex CLI rate-limit update.",
                            "summary_zh": "来源描述同一 Codex CLI 速率限制更新。",
                            "event_tag": "product_tool_update",
                            "entity_ids": ["openai"],
                            "importance_score": 83,
                        },
                    )(),
                )
            ]

        def match_existing_event(self, candidate_event, existing_events):
            self.merge_candidates.append((candidate_event, existing_events))
            return existing_events[0].event_key if existing_events else None

    class FakeFeed:
        entries = [
            {
                "id": str(index),
                "title": f"OpenAI Codex CLI rate limit update source {index}",
                "summary": "The source describes clearer rate limit controls for Codex CLI.",
                "published": f"Fri, 15 May 2026 09:3{min(index, 9)}:00 GMT",
            }
            for index in range(1, 7)
        ]

    def fake_parse(url):
        return FakeFeed()

    import feedparser

    monkeypatch.setattr(feedparser, "parse", fake_parse)
    repository = FakeRepository()
    synthesizer = FakeSynthesizer()
    service = RssIngestService(repository, event_synthesizer=synthesizer)

    count = service.ingest_sources(
        [RssSource(domain="ai", name="x_list_ai", url="http://example.test/rss", platform="X")],
    )

    assert count == 6
    assert len(repository.events_by_key) == 1
    event = next(iter(repository.events_by_key.values()))
    assert event.source_count == 6
    assert event.last_seen_at == datetime(2026, 5, 15, 9, 36)
    assert len(synthesizer.merge_candidates) >= 1
    assert repository.merge_queries[-1][3] == datetime(2026, 5, 13, 9, 36)
