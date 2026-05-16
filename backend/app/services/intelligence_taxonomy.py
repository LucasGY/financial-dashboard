from __future__ import annotations

ENTITY_ALIASES: dict[str, tuple[str, ...]] = {
    "apple": ("apple", "aapl"),
    "openai": ("openai", "chatgpt", "codex", "sora"),
    "anthropic": ("anthropic", "claude"),
    "amazon": ("amazon", "amzn", "aws"),
    "google": ("google", "deepmind", "gemini"),
    "microsoft": ("microsoft", "msft", "azure", "github", "copilot"),
    "nvidia": ("nvidia", "nvda", "cuda"),
    "meta": ("meta", "llama"),
    "tesla": ("tesla", "tsla"),
    "berkshire": ("berkshire", "brk", "brk.b", "buffett"),
    "tsmc": ("tsmc", "taiwan semiconductor", "台积电"),
    "xai": ("xai", "grok"),
    "perplexity": ("perplexity",),
    "spx": ("spx", "s&p 500", "sp500"),
    "nasdaq": ("nasdaq", "qqq", "ndx", "nasdaq futures"),
    "us10y": ("us10y", "10y", "treasury yield", "yields", "美债"),
    "dxy": ("dxy", "dollar index"),
    "btc": ("btc", "bitcoin"),
}

ENTITY_DISPLAY: dict[str, dict[str, str | None]] = {
    "apple": {"name": "Apple", "ticker": "AAPL"},
    "openai": {"name": "OpenAI", "ticker": None},
    "anthropic": {"name": "Anthropic", "ticker": None},
    "amazon": {"name": "Amazon", "ticker": "AMZN"},
    "google": {"name": "Google", "ticker": "GOOGL"},
    "microsoft": {"name": "Microsoft", "ticker": "MSFT"},
    "nvidia": {"name": "NVIDIA", "ticker": "NVDA"},
    "meta": {"name": "Meta", "ticker": "META"},
    "tesla": {"name": "Tesla", "ticker": "TSLA"},
    "berkshire": {"name": "Berkshire Hathaway", "ticker": "BRK"},
    "tsmc": {"name": "TSMC", "ticker": "TSMC"},
    "xai": {"name": "xAI", "ticker": None},
    "perplexity": {"name": "Perplexity", "ticker": None},
    "spx": {"name": "S&P 500", "ticker": "SPX"},
    "nasdaq": {"name": "NASDAQ", "ticker": "NASDAQ"},
    "us10y": {"name": "US 10Y", "ticker": "US10Y"},
    "dxy": {"name": "Dollar Index", "ticker": "DXY"},
    "btc": {"name": "Bitcoin", "ticker": "BTC"},
}

FINANCE_DEFAULT_ENTITY_IDS = ["apple", "microsoft", "nvidia", "google", "amazon", "meta", "tesla", "berkshire", "tsmc"]


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
            labels.append(f"{name} - {ticker}")
        else:
            labels.append(name)
    return labels


def normalize_event_tags_for_domain(domain: str, event_tags: list[str]) -> list[str]:
    if domain != "finance":
        return event_tags[:1] if event_tags else []
    cleaned = [tag for tag in event_tags if tag != "market"]
    return cleaned[:1] if cleaned else ["kol_opinion"]


def _dedupe(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
