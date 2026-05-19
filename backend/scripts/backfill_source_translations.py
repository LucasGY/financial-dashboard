from __future__ import annotations

import argparse
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings
from app.core.database import Database
from app.repositories.intelligence_feed_repository import IntelligenceFeedRepository
from app.services.event_synthesis_service import EventSynthesisService
from app.services.llm.providers.openai_compatible import OpenAICompatibleProvider


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill Chinese source-level translations for intelligence sources.")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=5)
    args = parser.parse_args()

    settings = get_settings()
    provider = OpenAICompatibleProvider(settings)
    if not provider.is_configured():
        raise SystemExit("LLM is required. Set FD_LLM_API_KEY/API_KEY and FD_LLM_MODEL/MODEL.")

    repository = IntelligenceFeedRepository(Database(settings))
    synthesizer = EventSynthesisService(provider)
    sources = repository.fetch_sources_missing_translations(limit=args.limit)
    updated = 0

    for chunk in _chunks(sources, max(1, args.batch_size)):
        payload = [
            {
                "id": f"source:{source.id}",
                "external_id": source.external_id,
                "source_platform": source.source_platform,
                "source_type": source.source_type,
                "author_name": source.author_name,
                "title": source.title,
                "summary": source.summary or "",
                "raw_content": source.raw_content or "",
            }
            for source in chunk
        ]
        translations = synthesizer.translate_sources(payload)
        for source in chunk:
            translated = translations.get(source.external_id) or translations.get(f"source:{source.id}") or {}
            if not translated:
                continue
            repository.update_source_translation(
                source_id=source.id,
                title_zh=translated.get("title_zh") or source.title_zh or "",
                summary_zh=translated.get("summary_zh") or source.summary_zh or "",
                raw_content_zh=translated.get("raw_content_zh") or source.raw_content_zh or "",
            )
            updated += 1

    print(f"Backfilled {updated} source translations")


def _chunks(items, size: int):
    for index in range(0, len(items), size):
        yield items[index : index + size]


if __name__ == "__main__":
    main()
