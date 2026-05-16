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
    assert sources[0].platform == "Paper"
    assert sources[1].platform == "X"
