# RSS Source Roles And Assets Design

## Goal

Upgrade the RSS-to-event pipeline so X sources can carry extracted full text and media assets, events can distinguish primary sources from related discussions, repost/quote/reply relationships are preserved, and the frontend routes simple single-source events directly to the original site while using the drawer for multi-source or discussion-rich events.

## Scope

This design applies to RSS ingestion for AI in One and Finance in One. Deep Dive remains backed by second-brain / Obsidian and is not changed.

`raw_content` extraction is enhanced only for X sources. Non-X RSS sources continue to use the RSS title/summary fields already available from the feed.

## Source Model

Each `intelligence_event_source` gains role, relationship, and media metadata:

- `source_role`: `primary` or `related_discussion`
- `original_url`: canonical source URL when known
- `quoted_url`: URL of a quoted X post or referenced source when detected
- `reposted_url`: URL of a reposted X post when detected
- `reply_to_url`: URL of the parent X post when detected
- `assets`: JSON list of image/video assets
- `extracted_at`: timestamp when enhanced extraction ran
- `extraction_status`: `rss_only`, `extracted`, or `failed`

Asset shape:

```json
[
  {"type": "image", "url": "https://..."},
  {"type": "video", "url": "https://...", "thumbnail_url": "https://..."}
]
```

## Source Role Rules

Primary sources are sources that represent the original item being tracked:

- arXiv / Paper sources
- OpenAI RSS / Claude RSS / official feeds
- GitHub release-like feeds
- X original posts

Related discussions are sources that comment on or amplify another source:

- X reposts
- X quote posts
- X replies
- X posts where extracted metadata shows a quoted/reposted/replied source

The first version uses deterministic rules. LLM event synthesis receives `source_role` and relationship fields as context but does not own the role assignment.

## X Extraction

For X sources, ingestion should enrich the RSS item with the same kind of information used by `LucasGY/everything-clipper`: extracted post text, images, videos, and relationship URLs. The first implementation can use a local extractor interface with RSSHub/feed fields and HTML parsing where available; the interface should be isolated so a stronger everything-clipper-based extractor can replace it without changing the ingest service.

If extraction succeeds:

- `raw_content` becomes the extracted X text.
- `assets` contains extracted image/video URLs.
- relationship fields are populated when present.
- `extraction_status = "extracted"`.

If extraction fails:

- fallback to current RSS title/summary logic.
- `assets = []`.
- `extraction_status = "failed"` or `rss_only`.

## Reposts, Quotes, Replies

When the current RSS item is a repost, quote, or reply:

- keep the current X post as a source.
- set `source_role = "related_discussion"`.
- preserve the relationship URL in `quoted_url`, `reposted_url`, or `reply_to_url`.
- do not manufacture a new source row for the referenced post unless the extractor can provide a stable external ID and text.

If the referenced original post is also present in RSS ingestion, normal `external_id` dedupe and event merge will attach both to the same event.

## LLM Event Synthesis

LLM batch input includes:

```json
{
  "source_id": "...",
  "source_role": "primary",
  "source_platform": "X",
  "author_name": "...",
  "source_date": "...",
  "raw_title": "...",
  "raw_content": "...",
  "assets_count": 2,
  "quoted_url": null,
  "reposted_url": null,
  "reply_to_url": null
}
```

Prompt guidance:

- primary sources define the event fact.
- related discussions provide commentary and context.
- do not let a discussion-only source overwrite the factual title when a primary source is present.

## Frontend Behavior

Card click behavior:

- If an event has exactly one source, that source is `primary`, there are no related discussions, and `source_url` exists, clicking the card opens the original URL in a new tab.
- Otherwise, clicking the card opens the detail drawer.

Drawer source layout:

1. Event summary and tags
2. Primary sources
3. Related discussions

Each source card shows:

- platform/type/author/date
- role label
- title
- extracted/raw text
- assets preview
- relationship label if quote/repost/reply
- open original link

## Testing

Backend tests cover:

- X original source gets `source_role = primary`.
- X quote/repost/reply source gets `source_role = related_discussion`.
- X extracted text replaces RSS duplicate title/summary.
- assets and relationship URLs persist through repository/API mapping.
- LLM input includes role and relationship fields.

Frontend tests/build cover:

- single primary source card opens source URL.
- multi-source or discussion event opens drawer.
- drawer groups primary sources before related discussions.

