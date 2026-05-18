from __future__ import annotations

import json
from datetime import datetime
from html import unescape
from typing import Optional

from app.core.database import Database
from app.repositories.models import IntelligenceEventRow, IntelligenceSourceRow


class IntelligenceFeedRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def fetch_events(
        self,
        domain: str,
        event_tag: Optional[str],
        search: Optional[str],
        min_score: Optional[int] = None,
        entity_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[IntelligenceEventRow]:
        clauses = ["event.domain = %s"]
        params: list[object] = [domain]
        if event_tag and event_tag != "all":
            clauses.append("JSON_CONTAINS(event.event_tags, %s)")
            params.append(json.dumps(event_tag))
        if entity_id and entity_id != "all":
            clauses.append("JSON_CONTAINS(event.entity_ids, %s)")
            params.append(json.dumps(entity_id))
        if search:
            clauses.append("(event.title LIKE %s OR event.summary LIKE %s OR event.tldr_zh LIKE %s)")
            like = f"%{search}%"
            params.extend([like, like, like])
        if min_score is not None:
            clauses.append("event.importance_score >= %s")
            params.append(min_score)
        params.append(limit)
        sql = f"""
            SELECT event.*,
                   COUNT(source.id) AS source_count,
                   SUM(CASE WHEN source.source_role = 'related_discussion' THEN 1 ELSE 0 END) AS related_discussion_count,
                   primary_source.id AS primary_source_id,
                   primary_source.event_id AS primary_source_event_id,
                   primary_source.external_id AS primary_source_external_id,
                   primary_source.source_name AS primary_source_name,
                   primary_source.source_platform AS primary_source_platform,
	                   primary_source.source_type AS primary_source_type,
	                   primary_source.source_url AS primary_source_url,
	                   primary_source.source_role AS primary_source_role,
	                   primary_source.original_url AS primary_source_original_url,
	                   primary_source.quoted_url AS primary_source_quoted_url,
	                   primary_source.reposted_url AS primary_source_reposted_url,
	                   primary_source.reply_to_url AS primary_source_reply_to_url,
	                   primary_source.assets AS primary_source_assets,
	                   primary_source.extracted_at AS primary_source_extracted_at,
	                   primary_source.extraction_status AS primary_source_extraction_status,
	                   primary_source.author_avatar_url AS primary_source_author_avatar_url,
	                   primary_source.author_name AS primary_source_author_name,
                   primary_source.source_date AS primary_source_date,
                   primary_source.title AS primary_source_title,
                   primary_source.summary AS primary_source_summary,
                   primary_source.raw_content AS primary_source_raw_content
            FROM intelligence_event event
            LEFT JOIN intelligence_event_source source ON source.event_id = event.id
            LEFT JOIN intelligence_event_source primary_source ON primary_source.id = (
                SELECT inner_source.id
                FROM intelligence_event_source inner_source
                WHERE inner_source.event_id = event.id
                ORDER BY CASE WHEN inner_source.source_role = 'primary' THEN 0 ELSE 1 END,
                         inner_source.source_date DESC,
                         inner_source.id DESC
                LIMIT 1
            )
            WHERE {' AND '.join(clauses)}
            GROUP BY event.id, primary_source.id
            ORDER BY event.last_seen_at DESC, event.importance_score DESC
            LIMIT %s
        """
        with self._database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(sql, params)
            return [self._map_event_row(row) for row in cursor.fetchall()]

    def fetch_event(self, event_id: int) -> Optional[IntelligenceEventRow]:
        rows = self.fetch_events_by_ids([event_id])
        return rows[0] if rows else None

    def fetch_events_by_ids(self, event_ids: list[int]) -> list[IntelligenceEventRow]:
        if not event_ids:
            return []
        placeholders = ", ".join(["%s"] * len(event_ids))
        sql = f"""
            SELECT event.*, COUNT(source.id) AS source_count
                   , SUM(CASE WHEN source.source_role = 'related_discussion' THEN 1 ELSE 0 END) AS related_discussion_count
            FROM intelligence_event event
            LEFT JOIN intelligence_event_source source ON source.event_id = event.id
            WHERE event.id IN ({placeholders})
            GROUP BY event.id
        """
        with self._database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(sql, event_ids)
            return [self._map_event_row(row) for row in cursor.fetchall()]

    def fetch_sources_for_event(self, event_id: int) -> list[IntelligenceSourceRow]:
        sql = """
            SELECT *
            FROM intelligence_event_source
            WHERE event_id = %s
            ORDER BY source_date DESC, id DESC
        """
        with self._database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(sql, [event_id])
            return [self._map_source_row(row) for row in cursor.fetchall()]

    def fetch_existing_source_external_ids(self, external_ids: list[str]) -> set[str]:
        if not external_ids:
            return set()
        placeholders = ", ".join(["%s"] * len(external_ids))
        sql = f"""
            SELECT external_id
            FROM intelligence_event_source
            WHERE external_id IN ({placeholders})
        """
        with self._database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(sql, external_ids)
            return {str(row["external_id"]) for row in cursor.fetchall()}

    def fetch_recent_merge_candidates(
        self,
        *,
        domain: str,
        event_tag: str,
        entity_ids: list[str],
        since: datetime,
        limit: int = 12,
    ) -> list[IntelligenceEventRow]:
        clauses = [
            "event.domain = %s",
            "event.last_seen_at >= %s",
            "JSON_CONTAINS(event.event_tags, %s)",
        ]
        params: list[object] = [domain, since, json.dumps(event_tag)]
        if entity_ids:
            clauses.append("(" + " OR ".join(["JSON_CONTAINS(event.entity_ids, %s)"] * len(entity_ids)) + ")")
            params.extend(json.dumps(entity_id) for entity_id in entity_ids)
        params.append(limit)
        sql = f"""
            SELECT event.*, COUNT(source.id) AS source_count
            FROM intelligence_event event
            LEFT JOIN intelligence_event_source source ON source.event_id = event.id
            WHERE {' AND '.join(clauses)}
            GROUP BY event.id
            ORDER BY event.last_seen_at DESC, event.importance_score DESC
            LIMIT %s
        """
        with self._database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(sql, params)
            return [self._map_event_row(row) for row in cursor.fetchall()]

    def upsert_event_with_source(self, event: dict, source: dict) -> None:
        event_sql = """
            INSERT INTO intelligence_event (
                event_key, domain, title, title_zh, summary, tldr_zh, first_seen_at, last_seen_at,
                entity_ids, event_tags, topic_tags, importance_score, status
            ) VALUES (
                %(event_key)s, %(domain)s, %(title)s, %(title_zh)s, %(summary)s, %(tldr_zh)s,
                %(first_seen_at)s, %(last_seen_at)s, %(entity_ids)s, %(event_tags)s, %(topic_tags)s,
                %(importance_score)s, %(status)s
            )
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                title_zh = VALUES(title_zh),
                summary = VALUES(summary),
                tldr_zh = VALUES(tldr_zh),
                entity_ids = VALUES(entity_ids),
                event_tags = VALUES(event_tags),
                topic_tags = VALUES(topic_tags),
                last_seen_at = GREATEST(last_seen_at, VALUES(last_seen_at)),
                importance_score = VALUES(importance_score),
                updated_at = CURRENT_TIMESTAMP
        """
        select_sql = "SELECT id FROM intelligence_event WHERE event_key = %s"
        source_sql = """
	            INSERT INTO intelligence_event_source (
	                event_id, external_id, source_name, source_platform, source_type, source_url,
	                source_role, original_url, quoted_url, reposted_url, reply_to_url, assets, extracted_at,
	                extraction_status, author_avatar_url, author_name, source_date, title, summary, raw_content
	            ) VALUES (
	                %(event_id)s, %(external_id)s, %(source_name)s, %(source_platform)s, %(source_type)s,
	                %(source_url)s, %(source_role)s, %(original_url)s, %(quoted_url)s, %(reposted_url)s,
	                %(reply_to_url)s, %(assets)s, %(extracted_at)s, %(extraction_status)s, %(author_avatar_url)s,
	                %(author_name)s, %(source_date)s, %(title)s, %(summary)s, %(raw_content)s
	            )
	            ON DUPLICATE KEY UPDATE
	                source_url = VALUES(source_url),
	                source_role = VALUES(source_role),
	                original_url = VALUES(original_url),
	                quoted_url = VALUES(quoted_url),
	                reposted_url = VALUES(reposted_url),
	                reply_to_url = VALUES(reply_to_url),
	                assets = VALUES(assets),
	                extracted_at = VALUES(extracted_at),
	                extraction_status = VALUES(extraction_status),
	                author_avatar_url = VALUES(author_avatar_url),
	                author_name = VALUES(author_name),
                title = VALUES(title),
                summary = VALUES(summary),
                raw_content = VALUES(raw_content),
                updated_at = CURRENT_TIMESTAMP
        """
        event_payload = {
            **event,
            "entity_ids": json.dumps(event["entity_ids"], ensure_ascii=False),
            "event_tags": json.dumps(event["event_tags"], ensure_ascii=False),
            "topic_tags": json.dumps(event["topic_tags"], ensure_ascii=False),
        }
        with self._database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(event_sql, event_payload)
            cursor.execute(select_sql, [event["event_key"]])
            row = cursor.fetchone()
            if not row:
                return
            cursor.execute(source_sql, _source_payload({**source, "event_id": row["id"]}))

    @staticmethod
    def _map_event_row(row: dict) -> IntelligenceEventRow:
        primary_source = None
        if row.get("primary_source_id") is not None:
            primary_source = IntelligenceSourceRow(
                id=int(row["primary_source_id"]),
                event_id=int(row["primary_source_event_id"]),
                external_id=str(row["primary_source_external_id"]),
                source_name=str(row["primary_source_name"]),
                source_platform=str(row["primary_source_platform"]),
	                source_type=str(row["primary_source_type"]),
	                source_url=row.get("primary_source_url"),
	                source_role=str(row.get("primary_source_role") or "primary"),
	                original_url=row.get("primary_source_original_url"),
	                quoted_url=row.get("primary_source_quoted_url"),
	                reposted_url=row.get("primary_source_reposted_url"),
	                reply_to_url=row.get("primary_source_reply_to_url"),
	                assets=_parse_assets(row.get("primary_source_assets")),
	                extracted_at=row.get("primary_source_extracted_at"),
	                extraction_status=row.get("primary_source_extraction_status"),
	                author_avatar_url=row.get("primary_source_author_avatar_url"),
	                author_name=row.get("primary_source_author_name"),
                source_date=row["primary_source_date"],
                title=str(row["primary_source_title"]),
                summary=row.get("primary_source_summary"),
                raw_content=row.get("primary_source_raw_content"),
            )
        return IntelligenceEventRow(
            id=int(row["id"]),
            event_key=str(row["event_key"]),
            domain=str(row["domain"]),
            title=str(row["title"]),
            title_zh=row.get("title_zh"),
            summary=str(row.get("summary") or ""),
            tldr_zh=row.get("tldr_zh"),
            first_seen_at=row["first_seen_at"],
            last_seen_at=row["last_seen_at"],
            entity_ids=json.loads(row.get("entity_ids") or "[]"),
            event_tags=json.loads(row.get("event_tags") or "[]"),
            topic_tags=json.loads(row.get("topic_tags") or "[]"),
            importance_score=int(row.get("importance_score") or 0),
            status=str(row.get("status") or "new"),
            source_count=int(row.get("source_count") or 0),
            related_discussion_count=int(row.get("related_discussion_count") or 0),
            primary_source=primary_source,
        )

    @staticmethod
    def _map_source_row(row: dict) -> IntelligenceSourceRow:
        return IntelligenceSourceRow(
            id=int(row["id"]),
            event_id=int(row["event_id"]),
            external_id=str(row["external_id"]),
            source_name=str(row["source_name"]),
            source_platform=str(row["source_platform"]),
	            source_type=str(row["source_type"]),
	            source_url=row.get("source_url"),
	            source_role=str(row.get("source_role") or "primary"),
	            original_url=row.get("original_url"),
	            quoted_url=row.get("quoted_url"),
	            reposted_url=row.get("reposted_url"),
	            reply_to_url=row.get("reply_to_url"),
	            assets=_parse_assets(row.get("assets")),
	            extracted_at=row.get("extracted_at"),
	            extraction_status=row.get("extraction_status"),
	            author_avatar_url=row.get("author_avatar_url"),
	            author_name=row.get("author_name"),
            source_date=row["source_date"],
            title=str(row["title"]),
            summary=row.get("summary"),
            raw_content=row.get("raw_content"),
        )


def _source_payload(source: dict) -> dict:
    return {
        **source,
        "source_role": source.get("source_role") or "primary",
        "original_url": source.get("original_url"),
        "quoted_url": source.get("quoted_url"),
        "reposted_url": source.get("reposted_url"),
        "reply_to_url": source.get("reply_to_url"),
        "assets": json.dumps(source.get("assets") or [], ensure_ascii=False),
        "extracted_at": source.get("extracted_at"),
        "extraction_status": source.get("extraction_status") or "rss_only",
    }


def _parse_assets(value: object) -> list[dict]:
    if isinstance(value, list):
        return [_normalize_asset(item) for item in value if isinstance(item, dict)]
    if not value:
        return []
    try:
        parsed = json.loads(str(value))
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    return [_normalize_asset(item) for item in parsed if isinstance(item, dict)]


def _normalize_asset(asset: dict) -> dict:
    normalized = dict(asset)
    if isinstance(normalized.get("url"), str):
        normalized["url"] = unescape(str(normalized["url"]))
    if isinstance(normalized.get("thumbnail_url"), str):
        normalized["thumbnail_url"] = unescape(str(normalized["thumbnail_url"]))
    return normalized
