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
            sources.append(RssSource(domain=domain, name=name, url=url, platform=_infer_platform(url)))
    return sources


def _infer_platform(url: str) -> str:
    lowered = url.lower()
    if "/twitter/" in lowered or "x.com" in lowered or "twitter.com" in lowered:
        return "X"
    if "arxiv.org" in lowered:
        return "Paper"
    return "RSS"
