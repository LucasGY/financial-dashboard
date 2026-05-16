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
from app.services.rss_ingest_service import RssIngestService
from app.services.rss_source_config import load_rss_sources


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest local RSS sources into intelligence events.")
    parser.add_argument("--limit-per-source", type=int, default=None)
    parser.add_argument(
        "--min-quality-threshold",
        type=int,
        default=None,
        help="Deprecated; ignored. RSS ingest only applies hard filters before LLM.",
    )
    parser.add_argument(
        "--min-rule-score",
        type=int,
        default=None,
        help="Deprecated; ignored. RSS ingest only applies hard filters before LLM.",
    )
    parser.add_argument("--use-llm", action="store_true", help="Deprecated; LLM event synthesis is now enabled by default.")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM synthesis for local debugging only.")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    sources = load_rss_sources(repo_root / ".rss")
    settings = get_settings()
    provider = OpenAICompatibleProvider(settings)
    if not args.no_llm and not provider.is_configured():
        raise SystemExit("LLM is required for RSS ingestion. Set FD_LLM_API_KEY/API_KEY and FD_LLM_MODEL/MODEL.")
    synthesizer = None if args.no_llm else EventSynthesisService(provider)
    service = RssIngestService(IntelligenceFeedRepository(Database(settings)), event_synthesizer=synthesizer)
    count = service.ingest_sources(
        sources,
        limit_per_source=args.limit_per_source,
    )
    print(f"Ingested {count} RSS entries")


if __name__ == "__main__":
    main()
