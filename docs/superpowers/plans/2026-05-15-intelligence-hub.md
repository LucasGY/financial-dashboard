# Intelligence Hub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade Entity Dynamics into an Intelligence Hub with Daily Digest, AI in One, Finance in One, and Deep Dive views.

**Architecture:** AI in One and Finance in One read high-frequency feed data from MariaDB, populated by RSS ingestion. RSS entries are normalized into source records, then grouped into deduplicated event records; the main feed renders events, and each event exposes all underlying sources. Deep Dive reads manual/high-quality notes from the production second-brain Obsidian vault and does not participate in RSS ingestion. The frontend consumes one normalized API contract so Sidebar and filters can switch views without caring which backend source produced the items.

**Tech Stack:** FastAPI, Pydantic, PyMySQL/MariaDB, python-frontmatter, feedparser, React, TypeScript, Tailwind, lucide-react.

---

## Source Configuration

Created local `.rss` in the repository root and added `.rss` to `.gitignore`.

`.rss` contents:

```ini
[ai]
arxiv_cs_ai_lg=https://rss.arxiv.org/rss/cs.ai+cs.lg
x_list_ai=http://49.51.253.23:1200/twitter/list/2010668465980424307

[finance]
x_list_finance=http://49.51.253.23:1200/twitter/list/2010668012806836322
```

Deep Dive is intentionally excluded from `.rss`. It reads from `FD_SECOND_BRAIN_PATH` on the production machine.

## Layout Requirements

Sidebar items:

- Daily Digest
- AI in One
- Finance in One
- Deep Dive

Top filter bar:

- AI in One: 全部, 模型发布 / 更新, 产品 / 工具更新, 行业动态, 论文研究, 技巧与观点
- Finance in One: 全部 + 实体标签筛选。默认显示七巨头、BRK、TSMC，其他实体进入下拉选择；实体标签必须按 canonical entity id 去重。
- Deep Dive: 访谈, 手动收藏, 精读笔记

Main Area:

- 当前频道标题
- 当前频道说明
- Top filter bar
- Search
- 日期时间线信息流，格式为 `yyyy-mm-dd hh:min | timeline | 事件卡片`
- 详情抽屉；打开后占据除 sidebar 外的主内容区域

RSS event pipeline:

- RSS 原始条目
- 清洗标准化
- 去重合并：LLM 对同一批候选源进行 cluster，输出去重事件和 source id 列表
- LLM 分类、摘要、打分：为每个去重事件生成 title、summary、单一 event tag、importance score
- 生成结构化 Item
- 按时间聚合
- 渲染成前端卡片

Event grouping requirement:

- AI in One and Finance in One render deduplicated events, not raw RSS entries.
- Each event includes every source that contributed to it.
- Event cards show the strongest source summary plus source count.
- The detail drawer shows all sources under that event, including X/RSS/arXiv/official/news links.
- If a card has one source, the source action opens the original URL directly.
- If a card has multiple sources, the source action opens source choices in the detail view.

## Label Taxonomy

The UI uses three distinct label concepts:

- Entity label: who this item affects.
- Event label: what happened.
- Source type: where the information came from or who produced it.

Entity storage rule:

- Store only canonical `entity_ids` in backend data.
- Do not store duplicate variants such as `Microsoft` and `MSFT` as separate tags.
- Render display labels by channel:
  - AI in One: company/product names, such as `Microsoft`, `OpenAI`, `Anthropic`.
  - Finance in One: tickers or market symbols, such as `MSFT`, `NVDA`, `GOOGL`.
  - Deep Dive: combined labels, such as `Microsoft · MSFT`.

Event labels:

- AI in One uses exactly these top-level event filters:
  - `model_release`: 模型发布 / 更新
  - `product_tool_update`: 产品 / 工具更新
  - `industry`: 行业动态
  - `paper_research`: 论文研究
  - `tips_opinion`: 技巧与观点
- Finance in One does not use event labels as the top filter. It uses canonical entity filters:
  - Primary chips: `apple`, `microsoft`, `nvidia`, `google`, `amazon`, `meta`, `tesla`, `berkshire`, `tsmc`
  - Display labels: `AAPL`, `MSFT`, `NVDA`, `GOOGL`, `AMZN`, `META`, `TSLA`, `BRK`, `TSMC`
  - Other entities are exposed through a dropdown.
  - Finance events can still store one internal event tag, currently `kol_opinion`, `macro`, or `company_industry`.
- Deep Dive uses exactly these top-level event filters:
  - `interview`: 访谈
  - `manual_saved`: 手动收藏
  - `close_reading`: 精读笔记

Source type rule:

- Keep two source fields:
  - `source_platform`: the transport/platform, such as `X`, `RSS`, `Blog`, `Changelog`, `Podcast`, `YouTube`, `Paper`, `Manual`.
  - `source_type`: the producer role, such as `Official`, `Founder`, `Researcher`, `Engineer`, `KOL`, `Media`, `Analyst`, `Community`, `Manual`.
- Cards can display them together, for example `X · KOL · @sama`, `Paper · Researcher · arXiv`, or `Manual · Obsidian`.

RSS/X content handling:

- RSS parsing receives the item title, summary/content, link, author, and published timestamp from the RSS endpoint.
- For X RSS entries, treat the RSS item body as the canonical captured tweet text for v1.
- X RSS often has identical `title` and `description`; when LLM is enabled, X items must use LLM synthesis for readable event title/summary rather than rendering duplicate raw text.
- Preserve `source_url` so the drawer can link back to the original X post.
- Add an extractor boundary so richer X content capture can later follow the pattern from `LucasGY/everything-clipper`: capture normalized page/post content separately from the UI, store the raw extracted text, then run downstream classification/deduplication on that stable text.
- I could not inspect `LucasGY/everything-clipper` from this environment because the GitHub fetch was blocked by the local proxy, so the plan references its expected clipper-style architecture rather than copying implementation details.

## File Structure

- Create `backend/database/schema/intelligence_feed.sql`: MariaDB schema for deduplicated events and underlying source records.
- Create `backend/app/repositories/intelligence_feed_repository.py`: MariaDB repository for AI/finance events and source records.
- Modify `backend/app/repositories/models.py`: add `IntelligenceEventRow` and `IntelligenceSourceRow` dataclasses.
- Modify `backend/app/schemas/entity_dynamics.py`: replace/extend feed schemas with normalized `IntelligenceItem`, filters, and detail response.
- Create `backend/app/services/rss_source_config.py`: parse `.rss` into typed source definitions.
- Create `backend/app/services/intelligence_taxonomy.py`: canonical domains, filters, source types, entity aliases, and event tags.
- Create `backend/app/services/rss_ingest_service.py`: fetch RSS, normalize raw entries, classify with deterministic rules, deduplicate into events, and upsert event/source records into MariaDB.
- Create `backend/app/services/content_extractors.py`: source extractor boundary for RSS and future X/page clipping.
- Create `backend/scripts/ingest_rss_sources.py`: CLI entrypoint for scheduled ingestion.
- Modify `backend/app/services/entity_dynamics_service.py`: orchestrate MariaDB AI/finance + second-brain Deep Dive.
- Modify `backend/app/api/dependencies.py`: inject repository/database into `EntityDynamicsService`.
- Modify `backend/app/api/v1/entity_dynamics.py`: add query params for channel/filter/search and keep detail endpoint.
- Modify `backend/app/api/v1/entity_dynamics.py`: support `entity` query param for Finance entity filtering.
- Create/modify `backend/tests/test_entity_dynamics_api.py`: API contract and filtering tests.
- Modify `backend/requirements.txt`: add `feedparser`.
- Modify `frontend/src/features/entity-dynamics/types.ts`: normalized frontend contract.
- Modify `frontend/src/features/entity-dynamics/api.ts`: query-aware feed endpoint.
- Modify `frontend/src/features/entity-dynamics/hooks.ts`: accept feed query params.
- Modify `frontend/src/pages/entities/EntitiesPage.tsx`: AIHOT-style shell with Sidebar and active view state.
- Modify `frontend/src/features/entity-dynamics/components/EntityFeed.tsx`: reusable information feed with date groups.
- Create `frontend/src/features/entity-dynamics/components/IntelligenceSidebar.tsx`: Daily Digest / AI in One / Finance in One / Deep Dive nav.
- Create `frontend/src/features/entity-dynamics/components/TopFilterBar.tsx`: channel-specific filters and search.
- Modify `frontend/src/features/entity-dynamics/components/EntityDrawer.tsx`: render normalized details from both MariaDB and second-brain.

---

### Task 1: Database Schema for Events and Sources

**Files:**
- Create: `backend/database/schema/intelligence_feed.sql`

- [ ] **Step 1: Add schema file**

Create `backend/database/schema/intelligence_feed.sql`:

```sql
CREATE TABLE IF NOT EXISTS intelligence_event (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    event_key VARCHAR(255) NOT NULL,
    domain VARCHAR(32) NOT NULL,
    title TEXT NOT NULL,
    title_zh TEXT NULL,
    summary TEXT NOT NULL,
    tldr_zh TEXT NULL,
    first_seen_at DATETIME NOT NULL,
    last_seen_at DATETIME NOT NULL,
    entity_ids JSON NOT NULL,
    event_tags JSON NOT NULL,
    topic_tags JSON NOT NULL,
    importance_score INT NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'new',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_intelligence_event_key (event_key),
    KEY idx_intelligence_event_domain_date (domain, last_seen_at),
    KEY idx_intelligence_event_importance (importance_score)
);

CREATE TABLE IF NOT EXISTS intelligence_event_source (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    event_id BIGINT UNSIGNED NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    source_name VARCHAR(128) NOT NULL,
    source_platform VARCHAR(64) NOT NULL,
    source_type VARCHAR(64) NOT NULL,
    source_url TEXT NULL,
    author_name VARCHAR(255) NULL,
    source_date DATETIME NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NULL,
    raw_content MEDIUMTEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_intelligence_source_external_id (external_id),
    KEY idx_intelligence_source_event_id (event_id),
    KEY idx_intelligence_source_date (source_date),
    CONSTRAINT fk_intelligence_source_event
        FOREIGN KEY (event_id)
        REFERENCES intelligence_event(id)
        ON DELETE CASCADE
);
```

- [ ] **Step 2: Apply schema locally**

Run:

```bash
mysql -h "$FD_MARIADB_HOST" -P "${FD_MARIADB_PORT:-3306}" -u "$FD_MARIADB_USER" -p"$FD_MARIADB_PASSWORD" "$FD_MARIADB_DATABASE" < backend/database/schema/intelligence_feed.sql
```

Expected: command exits with status `0`.

- [ ] **Step 3: Commit**

```bash
git add backend/database/schema/intelligence_feed.sql
git commit -m "feat: add intelligence event tables"
```

### Task 2: Backend Schema Contract

**Files:**
- Modify: `backend/app/schemas/entity_dynamics.py`
- Test: `backend/tests/test_entity_dynamics_api.py`

- [ ] **Step 1: Write API contract test**

Create/replace `backend/tests/test_entity_dynamics_api.py` with:

```python
from datetime import datetime

from app.api.dependencies import get_entity_dynamics_service
from app.schemas.entity_dynamics import FeedResponse, IntelligenceItem, SourceDetail


class FakeEntityDynamicsService:
    def get_feed(self, channel="ai", filter_key="all", search=None):
        return FeedResponse(
            items=[
                IntelligenceItem(
                    id="event:1",
                    slug="event:1",
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
                    event_tags=["product_tool_update", "agent"],
                    topic_tags=["codex"],
                    importance_score=72,
                    source_count=2,
                    source_url="https://x.com/example/status/1",
                    status="new",
                )
            ]
        )

    def get_detail(self, item_id):
        return SourceDetail(
            id=item_id,
            slug=item_id,
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
            event_tags=["product_tool_update", "agent"],
            topic_tags=["codex"],
            importance_score=72,
            source_count=2,
            source_url="https://x.com/example/status/1",
            status="new",
            content="Raw source text",
            sources=[
                {
                    "id": "source:1",
                    "source_name": "x_list_ai",
                    "source_platform": "X",
                    "source_type": "KOL",
                    "author_name": "@example",
                    "source_date": "2026-05-15 09:30",
                    "title": "OpenAI ships a Codex update",
                    "summary": "Codex can be controlled from mobile ChatGPT.",
                    "source_url": "https://x.com/example/status/1",
                    "raw_content": "Raw source text",
                },
                {
                    "id": "source:2",
                    "source_name": "openai_changelog",
                    "source_platform": "Official",
                    "source_type": "Official",
                    "author_name": None,
                    "source_date": "2026-05-15 09:34",
                    "title": "Codex update",
                    "summary": "Official changelog entry.",
                    "source_url": "https://openai.com/changelog/example",
                    "raw_content": "Official source text",
                },
            ],
        )


def test_entity_dynamics_feed_contract(client):
    client.app.dependency_overrides[get_entity_dynamics_service] = lambda: FakeEntityDynamicsService()

    response = client.get("/api/v1/entity-dynamics/feed?channel=ai&filter=product_tool_update")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["channel"] == "ai"
    assert payload["items"][0]["source_kind"] == "feed"
    assert payload["items"][0]["entity_ids"] == ["openai"]
    assert payload["items"][0]["importance_score"] == 72


def test_entity_dynamics_detail_contract(client):
    client.app.dependency_overrides[get_entity_dynamics_service] = lambda: FakeEntityDynamicsService()

    response = client.get("/api/v1/entity-dynamics/sources/event%3A1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "event:1"
    assert payload["content"] == "Raw source text"
    assert len(payload["sources"]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd backend && pytest tests/test_entity_dynamics_api.py -v
```

Expected: FAIL because `IntelligenceItem` fields and query params do not exist yet.

- [ ] **Step 3: Implement schema**

Modify `backend/app/schemas/entity_dynamics.py`:

```python
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


Channel = Literal["daily", "ai", "finance", "deep_dive"]
SourceKind = Literal["feed", "manual", "digest"]

class IntelligenceSource(BaseModel):
    id: str
    source_name: Optional[str] = None
    source_platform: Optional[str] = None
    source_type: Optional[str] = None
    author_name: Optional[str] = None
    source_date: str
    title: str
    summary: str = ""
    source_url: Optional[str] = None
    raw_content: str = ""


class IntelligenceItem(BaseModel):
    id: str
    slug: str
    channel: Channel
    domain: str
    source_kind: SourceKind
    source_platform: Optional[str] = None
    source_type: Optional[str] = None
    source_name: Optional[str] = None
    author_name: Optional[str] = None
    source_date: str
    title: str
    title_zh: str = ""
    summary: str = ""
    tldr_zh: str = ""
    tldr_en: str = ""
    entity_ids: list[str]
    entity_labels: list[str]
    event_tags: list[str]
    topic_tags: list[str]
    importance_score: Optional[int] = None
    source_count: int = 1
    source_url: Optional[str] = None
    status: str = "new"


class FeedResponse(BaseModel):
    items: list[IntelligenceItem]


class SourceDetail(IntelligenceItem):
    content: str
    sources: list[IntelligenceSource] = []
```

- [ ] **Step 4: Update API query params**

Modify `backend/app/api/v1/entity_dynamics.py`:

```python
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_entity_dynamics_service
from app.schemas.entity_dynamics import FeedResponse, SourceDetail
from app.services.entity_dynamics_service import EntityDynamicsService

router = APIRouter()


@router.get("/feed", response_model=FeedResponse)
def get_feed(
    channel: str = Query(default="ai"),
    filter: str = Query(default="all"),
    search: Optional[str] = Query(default=None),
    service: EntityDynamicsService = Depends(get_entity_dynamics_service),
) -> FeedResponse:
    return service.get_feed(channel=channel, filter_key=filter, search=search)


@router.get("/sources/{slug}", response_model=SourceDetail)
def get_source_detail(
    slug: str,
    service: EntityDynamicsService = Depends(get_entity_dynamics_service),
) -> SourceDetail:
    detail = service.get_detail(slug)
    if detail is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return detail
```

- [ ] **Step 5: Run test**

Run:

```bash
cd backend && pytest tests/test_entity_dynamics_api.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/entity_dynamics.py backend/app/api/v1/entity_dynamics.py backend/tests/test_entity_dynamics_api.py
git commit -m "feat: normalize entity dynamics API contract"
```

### Task 3: RSS Source Parser

**Files:**
- Create: `backend/app/services/rss_source_config.py`
- Test: `backend/tests/test_rss_source_config.py`

- [ ] **Step 1: Write parser tests**

Create `backend/tests/test_rss_source_config.py`:

```python
from pathlib import Path

from app.services.rss_source_config import load_rss_sources


def test_load_rss_sources_groups_domains(tmp_path: Path):
    rss_file = tmp_path / ".rss"
    rss_file.write_text(
        "[ai]\n"
        "arxiv_cs_ai_lg=https://rss.arxiv.org/rss/cs.ai+cs.lg\n"
        "x_list_ai=http://49.51.253.23:1200/twitter/list/2010668465980424307\n"
        "\n"
        "[finance]\n"
        "x_list_finance=http://49.51.253.23:1200/twitter/list/2010668012806836322\n",
        encoding="utf-8",
    )

    sources = load_rss_sources(rss_file)

    assert [source.domain for source in sources] == ["ai", "ai", "finance"]
    assert sources[0].name == "arxiv_cs_ai_lg"
    assert sources[0].platform == "RSS"
    assert sources[1].platform == "X"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd backend && pytest tests/test_rss_source_config.py -v
```

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement parser**

Create `backend/app/services/rss_source_config.py`:

```python
from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RssSource:
    domain: str
    name: str
    url: str
    platform: str


def load_rss_sources(path: Path) -> list[RssSource]:
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(path, encoding="utf-8")
    sources: list[RssSource] = []
    for domain in parser.sections():
        for name, url in parser.items(domain):
            sources.append(
                RssSource(
                    domain=domain,
                    name=name,
                    url=url,
                    platform=_infer_platform(url),
                )
            )
    return sources


def _infer_platform(url: str) -> str:
    if "/twitter/" in url or "x.com" in url or "twitter.com" in url:
        return "X"
    if "arxiv.org" in url:
        return "Paper"
    return "RSS"
```

- [ ] **Step 4: Run test**

Run:

```bash
cd backend && pytest tests/test_rss_source_config.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/rss_source_config.py backend/tests/test_rss_source_config.py
git commit -m "feat: parse local RSS source config"
```

### Task 4: Taxonomy and Deterministic Classification

**Files:**
- Create: `backend/app/services/intelligence_taxonomy.py`
- Test: `backend/tests/test_intelligence_taxonomy.py`

- [ ] **Step 1: Write classification tests**

Create `backend/tests/test_intelligence_taxonomy.py`:

```python
from app.services.intelligence_taxonomy import classify_feed_item, entity_labels_for_channel


def test_classify_openai_product_update():
    result = classify_feed_item(
        domain="ai",
        source_platform="X",
        title="OpenAI releases new Codex tools for ChatGPT",
        summary="Codex can now run tasks from ChatGPT mobile.",
    )

    assert result.entity_ids == ["openai"]
    assert "product_tool_update" in result.event_tags
    assert result.source_platform == "X"
    assert result.source_type == "KOL"
    assert result.importance_score >= 50


def test_classify_finance_macro_item():
    result = classify_feed_item(
        domain="finance",
        source_platform="X",
        title="US10Y falls as Fed cut odds rise",
        summary="Nasdaq futures move higher after yields drop.",
    )

    assert result.entity_ids == ["us10y", "nasdaq"]
    assert "macro" in result.event_tags
    assert "market" in result.event_tags


def test_entity_labels_are_channel_specific():
    assert entity_labels_for_channel(["microsoft", "openai"], "ai") == ["Microsoft", "OpenAI"]
    assert entity_labels_for_channel(["microsoft", "nvidia"], "finance") == ["MSFT", "NVDA"]
    assert entity_labels_for_channel(["microsoft"], "deep_dive") == ["Microsoft · MSFT"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd backend && pytest tests/test_intelligence_taxonomy.py -v
```

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement taxonomy**

Create `backend/app/services/intelligence_taxonomy.py`:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Classification:
    entity_ids: list[str]
    event_tags: list[str]
    topic_tags: list[str]
    source_platform: str
    source_type: str
    importance_score: int


ENTITY_ALIASES: dict[str, tuple[str, ...]] = {
    "openai": ("openai", "chatgpt", "codex", "sora"),
    "anthropic": ("anthropic", "claude"),
    "google": ("google", "deepmind", "gemini"),
    "microsoft": ("microsoft", "msft", "azure", "github", "copilot"),
    "nvidia": ("nvidia", "nvda", "cuda"),
    "meta": ("meta", "llama"),
    "xai": ("xai", "grok"),
    "perplexity": ("perplexity",),
    "spx": ("spx", "s&p 500", "sp500"),
    "nasdaq": ("nasdaq", "qqq", "ndx"),
    "us10y": ("us10y", "10y", "treasury yield", "美债"),
    "dxy": ("dxy", "dollar index"),
    "btc": ("btc", "bitcoin"),
}

ENTITY_DISPLAY: dict[str, dict[str, str | None]] = {
    "openai": {"name": "OpenAI", "ticker": None},
    "anthropic": {"name": "Anthropic", "ticker": None},
    "google": {"name": "Google", "ticker": "GOOGL"},
    "microsoft": {"name": "Microsoft", "ticker": "MSFT"},
    "nvidia": {"name": "NVIDIA", "ticker": "NVDA"},
    "meta": {"name": "Meta", "ticker": "META"},
    "xai": {"name": "xAI", "ticker": None},
    "perplexity": {"name": "Perplexity", "ticker": None},
    "spx": {"name": "S&P 500", "ticker": "SPX"},
    "nasdaq": {"name": "NASDAQ", "ticker": "NASDAQ"},
    "us10y": {"name": "US 10Y", "ticker": "US10Y"},
    "dxy": {"name": "Dollar Index", "ticker": "DXY"},
    "btc": {"name": "Bitcoin", "ticker": "BTC"},
}

EVENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "model_release": ("model", "gpt", "claude", "llama", "benchmark"),
    "product_tool_update": ("product", "tool", "codex", "chatgpt", "api", "sdk", "release", "update"),
    "industry": ("industry", "market share", "adoption"),
    "paper_research": ("paper", "arxiv", "research", "benchmark"),
    "tips_opinion": ("tip", "how to", "观点", "thread"),
    "kol_opinion": ("观点", "thesis", "take", "opinion"),
    "macro": ("fed", "cpi", "inflation", "rates", "yield", "us10y", "美联储", "通胀"),
    "market": ("nasdaq", "spx", "futures", "risk", "volatility", "market"),
    "company_industry": ("earnings", "guidance", "revenue", "margin", "company"),
}

EVENT_LABELS: dict[str, str] = {
    "model_release": "模型发布 / 更新",
    "product_tool_update": "产品 / 工具更新",
    "industry": "行业动态",
    "paper_research": "论文研究",
    "tips_opinion": "技巧与观点",
    "kol_opinion": "KOL观点",
    "macro": "宏观",
    "market": "市场",
    "company_industry": "公司 / 行业",
    "interview": "访谈",
    "manual_saved": "手动收藏",
    "close_reading": "精读笔记",
}


def classify_feed_item(domain: str, source_platform: str, title: str, summary: str) -> Classification:
    text = f"{title} {summary}".lower()
    entity_ids = _dedupe(
        entity_id
        for entity_id, aliases in ENTITY_ALIASES.items()
        if any(alias.lower() in text for alias in aliases)
    )
    event_tags = _dedupe(
        event
        for event, keywords in EVENT_KEYWORDS.items()
        if any(keyword.lower() in text for keyword in keywords)
    )
    if domain == "ai" and not event_tags:
        event_tags = ["industry"]
    if domain == "finance" and not event_tags:
        event_tags = ["market"]
    importance_score = min(100, 30 + len(entity_ids) * 15 + len(event_tags) * 10)
    source_type = "KOL" if source_platform == "X" else source_platform
    return Classification(
        entity_ids=entity_ids,
        event_tags=event_tags,
        topic_tags=[],
        source_platform=source_platform,
        source_type=source_type,
        importance_score=importance_score,
    )


def entity_labels_for_channel(entity_ids: list[str], channel: str) -> list[str]:
    canonical_ids = ["microsoft" if entity_id == "msft" else entity_id for entity_id in entity_ids]
    labels: list[str] = []
    for entity_id in _dedupe(canonical_ids):
        display = ENTITY_DISPLAY.get(entity_id)
        if not display:
            continue
        name = str(display["name"])
        ticker = display["ticker"]
        if channel == "finance" and ticker:
            labels.append(str(ticker))
        elif channel == "deep_dive" and ticker:
            labels.append(f"{name} · {ticker}")
        else:
            labels.append(name)
    return labels


def _dedupe(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
```

- [ ] **Step 4: Run test**

Run:

```bash
cd backend && pytest tests/test_intelligence_taxonomy.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/intelligence_taxonomy.py backend/tests/test_intelligence_taxonomy.py
git commit -m "feat: add intelligence taxonomy"
```

### Task 5: MariaDB Repository

**Files:**
- Modify: `backend/app/repositories/models.py`
- Create: `backend/app/repositories/intelligence_feed_repository.py`
- Test: `backend/tests/test_intelligence_feed_repository.py`

- [ ] **Step 1: Add repository unit test with fake database**

Create `backend/tests/test_intelligence_feed_repository.py`:

```python
from contextlib import contextmanager
from datetime import datetime

from app.repositories.intelligence_feed_repository import IntelligenceFeedRepository


class FakeCursor:
    def __init__(self):
        self.sql = ""
        self.params = None

    def execute(self, sql, params=None):
        self.sql = sql
        self.params = params

    def fetchall(self):
        return [
            {
                "id": 1,
                "external_id": "x:1",
                "domain": "ai",
                "source_name": "x_list_ai",
                "source_platform": "X",
                "source_url": "https://x.com/example/status/1",
                "author_name": "@example",
                "source_date": datetime(2026, 5, 15, 9, 30),
                "title": "OpenAI update",
                "summary": "Codex update",
                "raw_content": "Raw text",
                "entity_ids": "[\"openai\"]",
                "event_tags": "[\"product_tool_update\"]",
                "topic_tags": "[]",
                "source_type": "KOL",
                "importance_score": 72,
                "status": "new",
            }
        ]


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()

    def cursor(self):
        return self.cursor_obj

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeDatabase:
    def __init__(self):
        self.connection_obj = FakeConnection()

    @contextmanager
    def connection(self):
        yield self.connection_obj


def test_fetch_items_maps_json_fields():
    database = FakeDatabase()
    repository = IntelligenceFeedRepository(database)

    rows = repository.fetch_items(domain="ai", event_tag=None, search=None, limit=20)

    assert rows[0].external_id == "x:1"
    assert rows[0].entity_ids == ["openai"]
    assert rows[0].event_tags == ["product_tool_update"]
    assert "domain = %s" in database.connection_obj.cursor_obj.sql
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd backend && pytest tests/test_intelligence_feed_repository.py -v
```

Expected: FAIL because repository does not exist.

- [ ] **Step 3: Add dataclass**

Append to `backend/app/repositories/models.py`:

```python
@dataclass(frozen=True)
class IntelligenceFeedRow:
    id: int
    external_id: str
    domain: str
    source_name: str
    source_platform: str
    source_url: Optional[str]
    author_name: Optional[str]
    source_date: object
    title: str
    summary: Optional[str]
    raw_content: Optional[str]
    entity_ids: list[str]
    event_tags: list[str]
    topic_tags: list[str]
    source_type: str
    importance_score: int
    status: str
```

- [ ] **Step 4: Implement repository**

Create `backend/app/repositories/intelligence_feed_repository.py`:

```python
from __future__ import annotations

import json
from typing import Optional

from app.core.database import Database
from app.repositories.models import IntelligenceFeedRow


class IntelligenceFeedRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def fetch_items(
        self,
        domain: str,
        event_tag: Optional[str],
        search: Optional[str],
        limit: int = 100,
    ) -> list[IntelligenceFeedRow]:
        clauses = ["domain = %s"]
        params: list[object] = [domain]
        if event_tag and event_tag != "all":
            clauses.append("JSON_CONTAINS(event_tags, %s)")
            params.append(json.dumps(event_tag))
        if search:
            clauses.append("(title LIKE %s OR summary LIKE %s OR raw_content LIKE %s)")
            like = f"%{search}%"
            params.extend([like, like, like])
        params.append(limit)
        sql = f"""
            SELECT *
            FROM intelligence_feed_item
            WHERE {' AND '.join(clauses)}
            ORDER BY source_date DESC, importance_score DESC
            LIMIT %s
        """
        with self._database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(sql, params)
            return [self._map_row(row) for row in cursor.fetchall()]

    def upsert_item(self, item: dict) -> None:
        sql = """
            INSERT INTO intelligence_feed_item (
                external_id, domain, source_name, source_platform, source_url, author_name,
                source_date, title, summary, raw_content, entity_ids, event_tags, topic_tags,
                source_type, importance_score, status
            ) VALUES (
                %(external_id)s, %(domain)s, %(source_name)s, %(source_platform)s, %(source_url)s, %(author_name)s,
                %(source_date)s, %(title)s, %(summary)s, %(raw_content)s, %(entity_ids)s, %(event_tags)s, %(topic_tags)s,
                %(source_type)s, %(importance_score)s, %(status)s
            )
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                summary = VALUES(summary),
                raw_content = VALUES(raw_content),
                entity_ids = VALUES(entity_ids),
                event_tags = VALUES(event_tags),
                topic_tags = VALUES(topic_tags),
                source_type = VALUES(source_type),
                importance_score = VALUES(importance_score),
                updated_at = CURRENT_TIMESTAMP
        """
        payload = {
            **item,
            "entity_ids": json.dumps(item["entity_ids"], ensure_ascii=False),
            "event_tags": json.dumps(item["event_tags"], ensure_ascii=False),
            "topic_tags": json.dumps(item["topic_tags"], ensure_ascii=False),
        }
        with self._database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(sql, payload)

    @staticmethod
    def _map_row(row: dict) -> IntelligenceFeedRow:
        return IntelligenceFeedRow(
            id=int(row["id"]),
            external_id=str(row["external_id"]),
            domain=str(row["domain"]),
            source_name=str(row["source_name"]),
            source_platform=str(row["source_platform"]),
            source_url=row.get("source_url"),
            author_name=row.get("author_name"),
            source_date=row["source_date"],
            title=str(row["title"]),
            summary=row.get("summary"),
            raw_content=row.get("raw_content"),
            entity_ids=json.loads(row.get("entity_ids") or "[]"),
            event_tags=json.loads(row.get("event_tags") or "[]"),
            topic_tags=json.loads(row.get("topic_tags") or "[]"),
            source_type=str(row["source_type"]),
            importance_score=int(row["importance_score"]),
            status=str(row["status"]),
        )
```

- [ ] **Step 5: Run test**

Run:

```bash
cd backend && pytest tests/test_intelligence_feed_repository.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/repositories/models.py backend/app/repositories/intelligence_feed_repository.py backend/tests/test_intelligence_feed_repository.py
git commit -m "feat: add intelligence feed repository"
```

### Task 6: RSS Ingestion

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/services/rss_ingest_service.py`
- Create: `backend/scripts/ingest_rss_sources.py`
- Test: `backend/tests/test_rss_ingest_service.py`

- [ ] **Step 1: Add dependency**

Append to `backend/requirements.txt`:

```text
feedparser==6.0.11
```

- [ ] **Step 2: Write ingest service test**

Create `backend/tests/test_rss_ingest_service.py`:

```python
from app.services.rss_ingest_service import normalize_entry
from app.services.rss_source_config import RssSource


def test_normalize_entry_classifies_and_preserves_source():
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
    assert item["entity_ids"] == ["openai"]
    assert "product_tool_update" in item["event_tags"]
```

- [ ] **Step 3: Run test to verify it fails**

Run:

```bash
cd backend && pytest tests/test_rss_ingest_service.py -v
```

Expected: FAIL because module does not exist.

- [ ] **Step 4: Implement ingest service**

Create `backend/app/services/rss_ingest_service.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from app.repositories.intelligence_feed_repository import IntelligenceFeedRepository
from app.services.intelligence_taxonomy import classify_feed_item
from app.services.rss_source_config import RssSource


class RssIngestService:
    def __init__(self, repository: IntelligenceFeedRepository) -> None:
        self._repository = repository

    def ingest_sources(self, sources: list[RssSource]) -> int:
        count = 0
        for source in sources:
            feed = feedparser.parse(source.url)
            for entry in feed.entries:
                self._repository.upsert_item(normalize_entry(source, entry))
                count += 1
        return count


def normalize_entry(source: RssSource, entry: dict) -> dict:
    title = str(entry.get("title") or "").strip()
    summary = str(entry.get("summary") or "").strip()
    link = str(entry.get("link") or entry.get("id") or "").strip()
    classification = classify_feed_item(
        domain=source.domain,
        source_platform=source.platform,
        title=title,
        summary=summary,
    )
    return {
        "external_id": str(entry.get("id") or link or f"{source.name}:{title}"),
        "domain": source.domain,
        "source_name": source.name,
        "source_platform": source.platform,
        "source_url": link or None,
        "author_name": entry.get("author"),
        "source_date": _parse_entry_date(entry),
        "title": title,
        "summary": summary,
        "raw_content": summary,
        "entity_ids": classification.entity_ids,
        "event_tags": classification.event_tags,
        "topic_tags": classification.topic_tags,
        "source_type": classification.source_type,
        "importance_score": classification.importance_score,
        "status": "new",
    }


def _parse_entry_date(entry: dict) -> datetime:
    published = entry.get("published") or entry.get("updated")
    if published:
        parsed = parsedate_to_datetime(str(published))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return datetime.utcnow()
```

- [ ] **Step 5: Add CLI script**

Create `backend/scripts/ingest_rss_sources.py`:

```python
from __future__ import annotations

from pathlib import Path

from app.api.dependencies import get_database
from app.core.config import get_settings
from app.repositories.intelligence_feed_repository import IntelligenceFeedRepository
from app.services.rss_ingest_service import RssIngestService
from app.services.rss_source_config import load_rss_sources


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    sources = load_rss_sources(repo_root / ".rss")
    service = RssIngestService(IntelligenceFeedRepository(get_database(get_settings())))
    count = service.ingest_sources(sources)
    print(f"Ingested {count} RSS entries")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run tests**

Run:

```bash
cd backend && pytest tests/test_rss_ingest_service.py tests/test_rss_source_config.py tests/test_intelligence_taxonomy.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/requirements.txt backend/app/services/rss_ingest_service.py backend/scripts/ingest_rss_sources.py backend/tests/test_rss_ingest_service.py
git commit -m "feat: ingest RSS sources into intelligence feed"
```

### Task 7: Unified Entity Dynamics Service

**Files:**
- Modify: `backend/app/services/entity_dynamics_service.py`
- Modify: `backend/app/api/dependencies.py`
- Test: `backend/tests/test_entity_dynamics_service.py`

- [ ] **Step 1: Write service tests**

Create `backend/tests/test_entity_dynamics_service.py`:

```python
from datetime import datetime
from pathlib import Path

from app.repositories.models import IntelligenceFeedRow
from app.services.entity_dynamics_service import EntityDynamicsService


class FakeFeedRepository:
    def fetch_items(self, domain, event_tag, search, limit=100):
        return [
            IntelligenceFeedRow(
                id=1,
                external_id="x:1",
                domain=domain,
                source_name="x_list_ai",
                source_platform="X",
                source_url="https://x.com/example/status/1",
                author_name="@example",
                source_date=datetime(2026, 5, 15, 9, 30),
                title="OpenAI update",
                summary="Codex update",
                raw_content="Raw text",
                entity_ids=["openai"],
                event_tags=["product_tool_update"],
                topic_tags=[],
                source_type="KOL",
                importance_score=72,
                status="new",
            )
        ]


def test_ai_feed_comes_from_mariadb_repository(tmp_path: Path):
    service = EntityDynamicsService(
        second_brain_path=str(tmp_path),
        intelligence_feed_repository=FakeFeedRepository(),
    )

    response = service.get_feed(channel="ai", filter_key="all", search=None)

    assert response.items[0].id == "feed:1"
    assert response.items[0].source_kind == "feed"
    assert response.items[0].entity_labels == ["OpenAI"]


def test_deep_dive_comes_from_second_brain(tmp_path: Path):
    source_dir = tmp_path / "wiki" / "sources"
    source_dir.mkdir(parents=True)
    (source_dir / "deep-note.md").write_text(
        "---\n"
        "frontend_category: deep_dive\n"
        "source_platform: Manual\n"
        "source_date: 2026-05-15 08:00\n"
        "content_type: article\n"
        "entity_ids:\n"
        "  - openai\n"
        "event_tags:\n"
        "  - manual_saved\n"
        "title_zh: 深度笔记\n"
        "tldr_zh: 这是一条手动收藏。\n"
        "---\n"
        "# Deep note\n\nBody",
        encoding="utf-8",
    )
    service = EntityDynamicsService(
        second_brain_path=str(tmp_path),
        intelligence_feed_repository=FakeFeedRepository(),
    )

    response = service.get_feed(channel="deep_dive", filter_key="all", search=None)

    assert response.items[0].id == "deep:deep-note"
    assert response.items[0].source_kind == "manual"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd backend && pytest tests/test_entity_dynamics_service.py -v
```

Expected: FAIL because service constructor and mapping do not match.

- [ ] **Step 3: Modify service constructor and mapping**

Update `backend/app/services/entity_dynamics_service.py` to keep existing markdown parsing helpers, then add:

```python
from app.repositories.intelligence_feed_repository import IntelligenceFeedRepository
from app.repositories.models import IntelligenceFeedRow
from app.services.intelligence_taxonomy import entity_labels_for_channel
```

Use constructor:

```python
def __init__(
    self,
    second_brain_path: str,
    intelligence_feed_repository: IntelligenceFeedRepository,
) -> None:
    self._sources_dir = Path(second_brain_path) / "wiki" / "sources"
    self._intelligence_feed_repository = intelligence_feed_repository
```

Use public methods:

```python
def get_feed(self, channel: str = "ai", filter_key: str = "all", search: Optional[str] = None) -> FeedResponse:
    if channel in {"ai", "finance"}:
        rows = self._intelligence_feed_repository.fetch_items(
            domain=channel,
            event_tag=None if filter_key == "all" else filter_key,
            search=search,
        )
        return FeedResponse(items=[self._map_feed_row(row, channel) for row in rows])
    if channel == "deep_dive":
        return FeedResponse(items=self._load_deep_dive(filter_key=filter_key, search=search))
    return FeedResponse(items=[])

def _map_feed_row(self, row: IntelligenceFeedRow, channel: str) -> IntelligenceItem:
    source_date = row.source_date.strftime("%Y-%m-%d %H:%M") if hasattr(row.source_date, "strftime") else str(row.source_date)
    return IntelligenceItem(
        id=f"feed:{row.id}",
        slug=f"feed:{row.id}",
        channel=channel,
        domain=row.domain,
        source_kind="feed",
        source_platform=row.source_platform,
        source_type=row.source_type,
        source_name=row.source_name,
        author_name=row.author_name,
        source_date=source_date,
        title=row.title,
        title_zh="",
        summary=row.summary or "",
        tldr_zh=row.summary or "",
        tldr_en=row.summary or "",
        entity_ids=row.entity_ids,
        entity_labels=entity_labels_for_channel(row.entity_ids, channel),
        event_tags=row.event_tags,
        topic_tags=row.topic_tags,
        importance_score=row.importance_score,
        source_url=row.source_url,
        status=row.status,
    )
```

- [ ] **Step 4: Update dependency injection**

Modify `backend/app/api/dependencies.py`:

```python
from app.repositories.intelligence_feed_repository import IntelligenceFeedRepository
```

Replace `get_entity_dynamics_service`:

```python
def get_entity_dynamics_service(database: Database = Depends(get_database)) -> EntityDynamicsService:
    return EntityDynamicsService(
        second_brain_path=get_settings().second_brain_path,
        intelligence_feed_repository=IntelligenceFeedRepository(database),
    )
```

- [ ] **Step 5: Run tests**

Run:

```bash
cd backend && pytest tests/test_entity_dynamics_service.py tests/test_entity_dynamics_api.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/entity_dynamics_service.py backend/app/api/dependencies.py backend/tests/test_entity_dynamics_service.py
git commit -m "feat: unify feed and deep dive sources"
```

### Task 8: Frontend Contract and API Hooks

**Files:**
- Modify: `frontend/src/features/entity-dynamics/types.ts`
- Modify: `frontend/src/features/entity-dynamics/api.ts`
- Modify: `frontend/src/features/entity-dynamics/hooks.ts`

- [ ] **Step 1: Update types**

Modify `frontend/src/features/entity-dynamics/types.ts`:

```ts
export type Channel = "daily" | "ai" | "finance" | "deep_dive";
export type SourceKind = "feed" | "manual" | "digest";

export interface FeedQuery {
  channel: Channel;
  filter?: string;
  search?: string;
}

export interface FeedItem {
  id: string;
  slug: string;
  channel: Channel;
  domain: string;
  source_kind: SourceKind;
  source_platform: string | null;
  source_type: string | null;
  source_name: string | null;
  author_name: string | null;
  source_date: string;
  title: string;
  title_zh: string;
  summary: string;
  tldr_zh: string;
  tldr_en: string;
  entity_ids: string[];
  entity_labels: string[];
  event_tags: string[];
  topic_tags: string[];
  importance_score: number | null;
  source_count: number;
  source_url: string | null;
  status: string;
}

export interface FeedResponse {
  items: FeedItem[];
}

export interface SourceDetail extends FeedItem {
  content: string;
  sources: IntelligenceSource[];
}

export interface IntelligenceSource {
  id: string;
  source_name: string | null;
  source_platform: string | null;
  source_type: string | null;
  author_name: string | null;
  source_date: string;
  title: string;
  summary: string;
  source_url: string | null;
  raw_content: string;
}
```

- [ ] **Step 2: Update API client**

Modify `frontend/src/features/entity-dynamics/api.ts`:

```ts
import { getJson } from "../../lib/api/client";
import type { FeedQuery, FeedResponse, SourceDetail } from "./types";

export const getEntityFeed = ({ channel, filter = "all", search = "" }: FeedQuery) => {
  const params = new URLSearchParams({ channel, filter });
  if (search.trim()) params.set("search", search.trim());
  return getJson<FeedResponse>(`/entity-dynamics/feed?${params.toString()}`);
};

export const getSourceDetail = (slug: string) =>
  getJson<SourceDetail>(`/entity-dynamics/sources/${encodeURIComponent(slug)}`);
```

- [ ] **Step 3: Update hook**

Modify `frontend/src/features/entity-dynamics/hooks.ts`:

```ts
import { useCallback } from "react";
import { getEntityFeed, getSourceDetail } from "./api";
import type { FeedQuery } from "./types";
import { useAsyncData } from "../../lib/hooks";

export function useEntityFeed(query: FeedQuery) {
  return useAsyncData(useCallback(() => getEntityFeed(query), [query.channel, query.filter, query.search]), [
    query.channel,
    query.filter,
    query.search,
  ]);
}

export function useSourceDetail(slug: string | null) {
  return useAsyncData(useCallback(() => (slug ? getSourceDetail(slug) : Promise.resolve(null)), [slug]), [slug]);
}
```

- [ ] **Step 4: Build frontend**

Run:

```bash
cd frontend && npm run build
```

Expected: FAIL until UI components are updated to pass query props.

- [ ] **Step 5: Commit after Task 9 passes**

Do not commit this task alone if the frontend is broken. Commit with Task 9.

### Task 9: AIHOT-Style Frontend Shell

**Files:**
- Modify: `frontend/src/pages/entities/EntitiesPage.tsx`
- Create: `frontend/src/features/entity-dynamics/components/IntelligenceSidebar.tsx`
- Create: `frontend/src/features/entity-dynamics/components/TopFilterBar.tsx`
- Modify: `frontend/src/features/entity-dynamics/components/EntityFeed.tsx`
- Modify: `frontend/src/features/entity-dynamics/components/EntityDrawer.tsx`

- [ ] **Step 1: Add Sidebar component**

Create `frontend/src/features/entity-dynamics/components/IntelligenceSidebar.tsx`:

```tsx
import { BookOpen, BrainCircuit, ChartCandlestick, Newspaper } from "lucide-react";
import type { Channel } from "../types";

const NAV_ITEMS: { id: Channel; label: string; Icon: React.ElementType }[] = [
  { id: "daily", label: "Daily Digest", Icon: Newspaper },
  { id: "ai", label: "AI in One", Icon: BrainCircuit },
  { id: "finance", label: "Finance in One", Icon: ChartCandlestick },
  { id: "deep_dive", label: "Deep Dive", Icon: BookOpen },
];

export function IntelligenceSidebar({
  activeChannel,
  onChange,
}: {
  activeChannel: Channel;
  onChange: (channel: Channel) => void;
}) {
  return (
    <aside className="w-full border-b border-slate-200 bg-white px-3 py-3 dark:border-slate-800 dark:bg-slate-950 lg:fixed lg:inset-y-0 lg:left-0 lg:w-64 lg:border-b-0 lg:border-r">
      <div className="mb-4 hidden px-2 text-sm font-bold tracking-tight text-slate-900 dark:text-white lg:block">
        Intelligence Hub
      </div>
      <nav className="flex gap-2 overflow-x-auto lg:flex-col lg:overflow-visible">
        {NAV_ITEMS.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => onChange(id)}
            className={`flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              activeChannel === id
                ? "bg-slate-900 text-white dark:bg-amber-400 dark:text-slate-950"
                : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-white"
            }`}
          >
            <Icon className="size-4" />
            {label}
          </button>
        ))}
      </nav>
    </aside>
  );
}
```

- [ ] **Step 2: Add filter bar**

Create `frontend/src/features/entity-dynamics/components/TopFilterBar.tsx`:

```tsx
import { Search } from "lucide-react";
import type { Channel } from "../types";

const FILTERS: Record<Channel, { id: string; label: string }[]> = {
  daily: [{ id: "all", label: "全部" }],
  ai: [
    { id: "all", label: "全部" },
    { id: "model_release", label: "模型发布 / 更新" },
    { id: "product_tool_update", label: "产品 / 工具更新" },
    { id: "industry", label: "行业动态" },
    { id: "paper_research", label: "论文研究" },
    { id: "tips_opinion", label: "技巧与观点" },
  ],
  finance: [
    { id: "all", label: "全部" },
    { id: "kol_opinion", label: "KOL观点" },
    { id: "macro", label: "宏观" },
    { id: "market", label: "市场" },
    { id: "company_industry", label: "公司 / 行业" },
  ],
  deep_dive: [
    { id: "all", label: "全部" },
    { id: "interview", label: "访谈" },
    { id: "manual_saved", label: "手动收藏" },
    { id: "close_reading", label: "精读笔记" },
  ],
};

export function TopFilterBar({
  channel,
  activeFilter,
  search,
  onFilterChange,
  onSearchChange,
}: {
  channel: Channel;
  activeFilter: string;
  search: string;
  onFilterChange: (filter: string) => void;
  onSearchChange: (search: string) => void;
}) {
  return (
    <div className="sticky top-0 z-20 border-b border-slate-200 bg-[#f8fafc]/95 px-4 py-3 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex flex-wrap gap-2">
          {FILTERS[channel].map((filter) => (
            <button
              key={filter.id}
              onClick={() => onFilterChange(filter.id)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                activeFilter === filter.id
                  ? "bg-slate-900 text-white dark:bg-amber-400 dark:text-slate-950"
                  : "bg-white text-slate-600 hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-400 dark:hover:text-white"
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>
        <label className="flex min-w-0 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900">
          <Search className="size-4 shrink-0" />
          <input
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="搜索标题/摘要..."
            className="min-w-0 flex-1 bg-transparent text-slate-900 outline-none placeholder:text-slate-400 dark:text-white"
          />
        </label>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Rework page shell**

Modify `frontend/src/pages/entities/EntitiesPage.tsx` to own `activeChannel`, `activeFilter`, `search`, and `selectedSlug`; render `IntelligenceSidebar`, `TopFilterBar`, `EntityFeed`, and `EntityDrawer`.

- [ ] **Step 4: Rework feed rendering**

Modify `EntityFeed` to accept:

```ts
interface Props {
  channel: Channel;
  filter: string;
  search: string;
  onSelectItem: (slug: string) => void;
  selectedSlug: string | null;
}
```

Render item metadata in this order:

```text
source_platform / source_type · author_name · source_date · importance_score
title_zh || title
tldr_zh || summary || tldr_en
entity_labels
event_tags
source_count
```

- [ ] **Step 5: Build frontend**

Run:

```bash
cd frontend && npm run build
```

Expected: PASS.

- [ ] **Step 6: Commit frontend**

```bash
git add frontend/src/pages/entities/EntitiesPage.tsx frontend/src/features/entity-dynamics
git commit -m "feat: redesign entity dynamics as intelligence hub"
```

### Task 10: End-to-End Verification

**Files:**
- No code changes expected.

- [ ] **Step 1: Run backend tests**

Run:

```bash
cd backend && pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Run frontend build**

Run:

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Run RSS ingest manually**

Run:

```bash
cd backend && python scripts/ingest_rss_sources.py
```

Expected: prints `Ingested N RSS entries` where `N` is greater than `0` when the RSS endpoints are reachable.

- [ ] **Step 4: Start app and inspect UI**

Run backend:

```bash
cd backend && uvicorn app.main:create_app --factory --reload --port 8000
```

Run frontend:

```bash
cd frontend && npm run dev
```

Open:

```text
http://localhost:5173/entities
```

Expected:

- Sidebar shows Daily Digest, AI in One, Finance in One, Deep Dive.
- AI in One displays feed items from MariaDB after ingest.
- Finance in One displays finance feed items from MariaDB after ingest.
- Deep Dive displays second-brain markdown items from `FD_SECOND_BRAIN_PATH`.
- Search and top filters update the visible feed.
- Detail drawer opens for feed and Deep Dive items.

## Self-Review

- Spec coverage: RSS config, AI/finance MariaDB storage, Deep Dive second-brain separation, unified API, Sidebar, channel filters, search, feed cards, and detail drawer are covered.
- Placeholder scan: no `TBD`, `TODO`, or unspecified tasks remain.
- Type consistency: `channel`, `source_kind`, `entity_ids`, `entity_labels`, `event_tags`, `importance_score`, and `source_platform` are consistently used across backend and frontend.
