# RSS Source Roles And Assets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add X source extraction metadata, primary/discussion source roles, repost/quote/reply handling, and source-aware card click/drawer behavior.

**Architecture:** Extend `intelligence_event_source` with role, relationship, and asset columns. Keep extraction behind a focused X extractor module so RSS ingestion stays responsible for orchestration. API schemas expose source role/assets to the frontend, and the frontend decides whether card clicks should open the original URL or the drawer.

**Tech Stack:** FastAPI, PyMySQL/MariaDB, feedparser, React/Vite/TypeScript, pytest.

---

### Task 1: Source Role And Asset Schema

**Files:**
- Modify: `backend/database/schema/intelligence_feed.sql`
- Modify: `backend/app/repositories/models.py`
- Modify: `backend/app/repositories/intelligence_feed_repository.py`
- Test: `backend/tests/test_entity_dynamics_api.py`

- [ ] Add source columns to schema:
  - `source_role VARCHAR(32) NOT NULL DEFAULT 'primary'`
  - `original_url TEXT NULL`
  - `quoted_url TEXT NULL`
  - `reposted_url TEXT NULL`
  - `reply_to_url TEXT NULL`
  - `assets JSON NOT NULL`
  - `extracted_at DATETIME NULL`
  - `extraction_status VARCHAR(32) NULL`

- [ ] Extend `IntelligenceSourceRow` with matching fields.

- [ ] Update repository insert/select/map logic to serialize `assets` as JSON and default missing fields safely.

- [ ] Update API fake contract test so a source includes role and assets.

- [ ] Run:

```bash
pytest -q backend/tests/test_entity_dynamics_api.py
```

Expected: pass.

### Task 2: X Extraction And Source Normalization

**Files:**
- Create: `backend/app/services/x_content_extractor.py`
- Modify: `backend/app/services/rss_ingest_service.py`
- Test: `backend/tests/test_rss_ingest_service.py`

- [ ] Create an extractor with return fields:

```python
{
    "text": "...",
    "assets": [{"type": "image", "url": "..."}],
    "quoted_url": None,
    "reposted_url": None,
    "reply_to_url": None,
    "status": "extracted",
}
```

- [ ] Implement first-pass extraction from RSSHub/feedparser fields:
  - text from `content`, `summary`, `description`, or `title`
  - media from `media_content`, `media_thumbnail`, `enclosures`, and `links`
  - relationship URLs from HTML/text links to `x.com/.../status/...`
  - role `related_discussion` when quote/repost/reply is detected

- [ ] In `normalize_entry`, use the extractor only for `source.platform == "X"`.

- [ ] Keep non-X behavior unchanged with `source_role = "primary"`, `assets = []`, and `extraction_status = "rss_only"`.

- [ ] Run:

```bash
pytest -q backend/tests/test_rss_ingest_service.py
```

Expected: pass.

### Task 3: LLM Input Uses Source Roles

**Files:**
- Modify: `backend/app/services/event_synthesis_service.py`
- Test: `backend/tests/test_event_synthesis_service.py`

- [ ] Add `source_role`, `assets_count`, `quoted_url`, `reposted_url`, and `reply_to_url` to batch LLM input.

- [ ] Update prompt to say primary sources define event facts and discussions provide context.

- [ ] Add a test that inspects the LLM prompt payload for these fields.

- [ ] Run:

```bash
pytest -q backend/tests/test_event_synthesis_service.py
```

Expected: pass.

### Task 4: API And Frontend Types

**Files:**
- Modify: `backend/app/schemas/entity_dynamics.py`
- Modify: `backend/app/services/entity_dynamics_service.py`
- Modify: `frontend/src/features/entity-dynamics/types.ts`
- Modify: `frontend/src/features/entity-dynamics/api.ts`
- Test: `backend/tests/test_entity_dynamics_service.py`

- [ ] Expose source role, relationship fields, assets, and `has_related_discussions` on feed/detail responses.

- [ ] Compute `has_related_discussions` from source rows where `source_role == "related_discussion"`.

- [ ] Update TypeScript types to match API.

- [ ] Run:

```bash
pytest -q backend/tests/test_entity_dynamics_service.py backend/tests/test_entity_dynamics_api.py
npm run build
```

Expected: pass.

### Task 5: Card Click And Drawer Grouping

**Files:**
- Modify: `frontend/src/features/entity-dynamics/components/EntityFeed.tsx`
- Modify: `frontend/src/features/entity-dynamics/components/EntityDrawer.tsx`

- [ ] Change card click:
  - one source
  - no related discussions
  - primary source
  - has `source_url`
  - open source URL in a new tab
  - otherwise open drawer

- [ ] Group drawer sources into Primary Sources and Related Discussions.

- [ ] Show source role, relationship labels, `raw_content`, and asset previews in each source card.

- [ ] Run:

```bash
npm run build
```

Expected: pass.

### Task 6: Full Verification

**Files:**
- No new files.

- [ ] Run backend tests:

```bash
pytest -q
```

Expected: all tests pass.

- [ ] Run frontend build:

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] Run a small ingest:

```bash
set -a
[ -f .db.env ] && . ./.db.env
[ -f .env ] && . ./.env
set +a
python backend/scripts/ingest_rss_sources.py --limit-per-source 2
```

Expected: command exits successfully and prints ingested count.

