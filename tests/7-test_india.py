from datetime import datetime, timezone
from pathlib import Path

from trend_radar.india import Topic, build_brief, match_niche, parse_google_rss, parse_youtube
from trend_radar.niches import keywords_for

SAMPLE = Path(__file__).resolve().parent / "google_trends_in_sample.xml"


def test_parse_google_rss_sample():
    topics = parse_google_rss(SAMPLE.read_text(encoding="utf-8"))
    assert len(topics) >= 5
    assert all(t.source == "google" and t.title for t in topics)
    assert any(t.traffic >= 1000 for t in topics)


def test_parse_youtube():
    data = {"items": [{"id": "abc", "snippet": {"title": "Asia Cup highlights", "channelTitle": "Star Sports",
                                                "categoryId": "17", "tags": ["Cricket"]},
                       "statistics": {"viewCount": "120000"}}]}
    t = parse_youtube(data)[0]
    assert t.traffic == 120000 and t.link.endswith("abc") and "cricket" in t.text


def test_match_niche_uses_headline_and_hindi():
    topics = [Topic("benjamin ito-davis", "google", headline="Japan-India wide call", context="Cricbuzz"),
              Topic("बारिश", "google", headline="भारी बारिश का अलर्ट"),
              Topic("paradise movie rating", "google")]
    assert [t.title for t in match_niche(topics, "cricket")] == ["benjamin ito-davis"]
    assert [t.title for t in match_niche(topics, "news")] == ["बारिश"]
    assert len(match_niche(topics, "all")) == 3


def test_keywords_extra():
    assert "nomadiq" in keywords_for("travel", ["Nomadiq"])


def test_brief_marks_new_and_ist():
    now = datetime(2026, 9, 24, 3, 30, tzinfo=timezone.utc)  # 9:00 AM IST
    g = [Topic("bse", "google", traffic=10000, headline="NSE IPO lists today"),
         Topic("ipo gmp", "google", traffic=2000)]
    text = build_brief("finance", g, [], seen_before={"bse"}, now=now)
    assert "09:00 AM IST" in text
    assert "- bse (10,000+ searches)" in text and "ipo gmp [NEW]" in text


def test_short_keywords_match_whole_words_only():
    topics = [Topic("heavy rain alert", "google"), Topic("new ai phone launch", "google")]
    assert [t.title for t in match_niche(topics, "tech")] == ["new ai phone launch"]
