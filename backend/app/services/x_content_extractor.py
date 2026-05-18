from __future__ import annotations

import re
from datetime import datetime, timezone
from html import unescape
from typing import Any


STATUS_URL_PATTERN = re.compile(r"https?://(?:www\.)?(?:x|twitter)\.com/[^/\"' <]+/status/\d+")


def extract_x_content(entry: dict) -> dict:
    html_text = _first_text(entry.get("content"), entry.get("summary_detail"), entry.get("summary"), entry.get("description"), entry.get("title"))
    text = _clean_text(html_text)
    relationships = _extract_relationship_urls(entry, html_text)
    return {
        "text": text,
        "assets": _extract_assets(entry, html_text),
        "quoted_url": relationships["quoted_url"],
        "reposted_url": relationships["reposted_url"],
        "reply_to_url": relationships["reply_to_url"],
        "status": "extracted" if text or relationships["quoted_url"] or relationships["reposted_url"] or relationships["reply_to_url"] else "rss_only",
        "extracted_at": datetime.now(timezone.utc).replace(tzinfo=None) if text else None,
    }


def infer_x_source_role(extracted: dict) -> str:
    if extracted.get("quoted_url") or extracted.get("reposted_url") or extracted.get("reply_to_url"):
        return "related_discussion"
    return "primary"


def _first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, list) and value:
            content_value = value[0].get("value") if isinstance(value[0], dict) else value[0]
            if content_value:
                return str(content_value)
        if isinstance(value, dict):
            content_value = value.get("value")
            if content_value:
                return str(content_value)
        if value:
            return str(value)
    return ""


def _clean_text(value: str) -> str:
    text = re.sub(r"<(br|p|div|li)[^>]*>", " ", value, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_relationship_urls(entry: dict, html_text: str) -> dict[str, str | None]:
    text = " ".join(str(value or "") for value in (entry.get("title"), entry.get("summary"), entry.get("description"), html_text))
    urls = [url for url in STATUS_URL_PATTERN.findall(text) if url != str(entry.get("link") or entry.get("id") or "")]
    lowered = text.lower()
    if not urls:
        return {"quoted_url": None, "reposted_url": None, "reply_to_url": None}
    if any(marker in lowered for marker in ("retweeted", "reposted", "转发", "retweeted by")):
        return {"quoted_url": None, "reposted_url": urls[0], "reply_to_url": None}
    if any(marker in lowered for marker in ("replying to", "回复", "in reply to")):
        return {"quoted_url": None, "reposted_url": None, "reply_to_url": urls[0]}
    return {"quoted_url": urls[0], "reposted_url": None, "reply_to_url": None}


def _extract_assets(entry: dict, html_text: str) -> list[dict]:
    assets: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for url in _media_urls_from_entry(entry):
        url = _clean_url(url)
        media_type = _asset_type(url)
        key = (media_type, url)
        if key not in seen:
            seen.add(key)
            assets.append({"type": media_type, "url": url})
    for url in re.findall(r"<img[^>]+src=[\"']([^\"']+)[\"']", html_text, flags=re.IGNORECASE):
        url = _clean_url(url)
        key = ("image", url)
        if key not in seen:
            seen.add(key)
            assets.append({"type": "image", "url": url})
    for url in re.findall(r"<video[^>]+src=[\"']([^\"']+)[\"']", html_text, flags=re.IGNORECASE):
        url = _clean_url(url)
        key = ("video", url)
        if key not in seen:
            seen.add(key)
            assets.append({"type": "video", "url": url})
    return assets


def _clean_url(url: str) -> str:
    return unescape(str(url)).strip()


def _media_urls_from_entry(entry: dict) -> list[str]:
    urls: list[str] = []
    for field in ("media_content", "media_thumbnail", "enclosures", "links"):
        values = entry.get(field) or []
        if not isinstance(values, list):
            continue
        for value in values:
            if not isinstance(value, dict):
                continue
            url = value.get("url") or value.get("href")
            media_type = str(value.get("type") or value.get("medium") or "")
            if url and _looks_like_media(str(url), media_type):
                urls.append(str(url))
    return urls


def _looks_like_media(url: str, media_type: str) -> bool:
    lowered = f"{url} {media_type}".lower()
    return any(token in lowered for token in ("image", "video", ".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".mov"))


def _asset_type(url: str) -> str:
    lowered = url.lower()
    if any(token in lowered for token in (".mp4", ".mov", "video")):
        return "video"
    return "image"
