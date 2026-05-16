from __future__ import annotations


def extract_rss_text(entry: dict) -> str:
    return str(entry.get("summary") or entry.get("description") or entry.get("title") or "").strip()
