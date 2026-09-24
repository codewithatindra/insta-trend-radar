"""India Pulse: what India is searching and watching right now, filtered to your niche.

Sources (all official or public, no login, no scraping of Instagram):
- google  : Google Trends "trending now" feed for India (trends.google.com/trending/rss?geo=IN).
            Free, no key. It is a public feed, not a documented API, so it may change.
- youtube : YouTube Data API v3 "most popular" chart for India (regionCode=IN).
            Needs a free API key (YOUTUBE_API_KEY). Each call costs 1 quota unit.

Topics come in English, Hindi, Telugu, Tamil and more, exactly as Indians search them.
"""
from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import requests

from .niches import keywords_for

GOOGLE_TRENDS_RSS = "https://trends.google.com/trending/rss"
YOUTUBE_VIDEOS = "https://www.googleapis.com/youtube/v3/videos"
HT = {"ht": "https://trends.google.com/trending/rss"}
IST = timezone(timedelta(hours=5, minutes=30))
USER_AGENT = "trend-radar-india/0.3 (+https://github.com/codewithatindra/insta-trend-radar)"


@dataclass
class Topic:
    title: str
    source: str               # "google" or "youtube"
    traffic: int = 0          # Google: approx searches (e.g. 10000+ -> 10000). YouTube: views.
    link: str = ""
    headline: str = ""        # news headline (Google) or channel name (YouTube)
    context: str = ""         # extra text used for niche matching (news source, tags, category)
    started: str = ""         # ISO time
    tags: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join([self.title, self.headline, self.context, " ".join(self.tags)]).lower()


def _traffic(value: str) -> int:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    return int(digits) if digits else 0


def parse_google_rss(xml_text: str) -> list[Topic]:
    root = ET.fromstring(xml_text)
    out: list[Topic] = []
    for it in root.iter("item"):
        news = it.findall("ht:news_item", HT)
        first = news[0] if news else None
        started = ""
        try:
            started = parsedate_to_datetime(it.findtext("pubDate") or "").isoformat()
        except (TypeError, ValueError):
            pass
        out.append(Topic(
            title=(it.findtext("title") or "").strip(),
            source="google",
            traffic=_traffic(it.findtext("ht:approx_traffic", namespaces=HT) or ""),
            link=(first.findtext("ht:news_item_url", namespaces=HT) if first is not None else "") or "",
            headline=(first.findtext("ht:news_item_title", namespaces=HT) if first is not None else "") or "",
            context=" ".join(filter(None, [
                n.findtext("ht:news_item_title", namespaces=HT) or "" for n in news[1:]
            ] + [n.findtext("ht:news_item_source", namespaces=HT) or "" for n in news])),
            started=started,
        ))
    return out


def google_trends(geo: str = "IN", session: requests.Session | None = None) -> list[Topic]:
    s = session or requests.Session()
    try:
        r = s.get(GOOGLE_TRENDS_RSS, params={"geo": geo}, headers={"User-Agent": USER_AGENT}, timeout=20)
        r.raise_for_status()
        return parse_google_rss(r.text)
    except (requests.RequestException, ET.ParseError) as e:
        print(f"  warning: Google Trends feed skipped ({e.__class__.__name__}: {e})")
        return []


# YouTube category IDs -> names, so "Sports" or "Music" can match a niche.
YT_CATEGORIES = {"1": "film animation", "2": "autos vehicles", "10": "music", "15": "pets animals",
                 "17": "sports cricket", "19": "travel", "20": "gaming", "22": "people blogs vlog",
                 "23": "comedy", "24": "entertainment", "25": "news politics", "26": "howto style",
                 "27": "education", "28": "science technology"}


def parse_youtube(data: dict) -> list[Topic]:
    out: list[Topic] = []
    for v in (data or {}).get("items", []):
        sn, st = v.get("snippet", {}), v.get("statistics", {})
        out.append(Topic(
            title=sn.get("title", ""), source="youtube", traffic=int(st.get("viewCount") or 0),
            link=f"https://www.youtube.com/watch?v={v.get('id', '')}", headline=sn.get("channelTitle", ""),
            context=YT_CATEGORIES.get(str(sn.get("categoryId", "")), ""),
            started=sn.get("publishedAt", ""), tags=[t.lower() for t in sn.get("tags", [])[:15]],
        ))
    return out


def youtube_trending(region: str = "IN", api_key: str | None = None, max_results: int = 50,
                     session: requests.Session | None = None) -> list[Topic]:
    key = api_key or os.getenv("YOUTUBE_API_KEY", "")
    if not key:
        print("  note: YouTube skipped (set YOUTUBE_API_KEY in .env to add India's trending videos)")
        return []
    s = session or requests.Session()
    try:
        r = s.get(YOUTUBE_VIDEOS, params={"part": "snippet,statistics", "chart": "mostPopular",
                                          "regionCode": region, "maxResults": min(max_results, 50),
                                          "key": key}, timeout=20)
        r.raise_for_status()
        return parse_youtube(r.json())
    except requests.RequestException as e:
        print(f"  warning: YouTube skipped ({e.__class__.__name__})")
        return []


def match_niche(topics: list[Topic], niche: str, extra_keywords: list[str] | None = None) -> list[Topic]:
    """Keep topics that mention one of the niche's keywords. niche "all" keeps everything."""
    if niche.lower() in ("all", "india", ""):
        return topics
    pattern = _keyword_pattern(keywords_for(niche, extra_keywords))
    return [t for t in topics if pattern.search(t.text)]


def _keyword_pattern(words: list[str]) -> "re.Pattern[str]":
    """English keywords match whole words only ("ai" must not match "rain"); Indian-script
    keywords match as substrings, since word boundaries don't work well for them."""
    parts = []
    for w in words:
        w = w.strip().lower()
        if not w:
            continue
        parts.append(rf"\b{re.escape(w)}\b" if w.isascii() else re.escape(w))
    return re.compile("|".join(parts) or r"(?!x)x")


def build_brief(niche: str, google: list[Topic], youtube: list[Topic], hashtags: list | None = None,
                seen_before: set[str] | None = None, top_n: int = 5, now: datetime | None = None) -> str:
    """Plain-text brief that reads well on Telegram, WhatsApp, Slack or email."""
    now = (now or datetime.now(timezone.utc)).astimezone(IST)
    seen_before = seen_before or set()
    label = "India" if niche.lower() in ("all", "india", "") else f"India - {niche}"
    lines = [f"Trend Radar {label} | {now:%a %d %b, %I:%M %p} IST", ""]

    def section(title: str, items: list[Topic], unit: str) -> None:
        lines.append(title)
        if not items:
            lines.append("  nothing matched this run")
        for t in sorted(items, key=lambda x: x.traffic, reverse=True)[:top_n]:
            fresh = " [NEW]" if t.title.lower() not in seen_before else ""
            lines.append(f"- {t.title}{fresh} ({t.traffic:,}+ {unit})")
            if t.headline:
                lines.append(f"  {t.headline[:140]}")
            if t.link:
                lines.append(f"  {t.link}")
        lines.append("")

    section("Searching on Google:", google, "searches")
    if youtube:
        section("Watching on YouTube:", youtube, "views")
    if hashtags:
        lines.append("Early hashtag signals (Bluesky/Mastodon, global):")
        lines += [f"- {h.summary()}" for h in hashtags[:top_n]]
        lines.append("")
    return "\n".join(lines).rstrip()
