"""Live data sources. Each returns a list of Post objects for a set of seed hashtags.

- bluesky   : Bluesky public API (api.bsky.app), no account or key needed.
- mastodon  : Mastodon public hashtag timelines (any instance), no account or key needed.
- instagram : official Instagram Graph API. Needs a Business/Creator account and Meta app
              approval (see README). Optional.

All of these are official public APIs. Nothing here logs in as a user or scrapes pages.
"""
from __future__ import annotations

import html
import os
import re
import time
from typing import Iterable

import requests

from .graph_api import InstagramGraphClient, Post

USER_AGENT = "insta-trend-radar/0.2 (+https://github.com/codewithatindra/insta-trend-radar)"
TAG_RE = re.compile(r"<[^>]+>")


def _get_json(s: requests.Session, url: str, params: dict, tries: int = 4):
    """GET with a short backoff. Returns None (and prints a warning) if the source keeps failing,
    so one flaky source never kills the whole run."""
    for attempt in range(tries):
        try:
            r = s.get(url, params=params, timeout=20)
            if r.status_code in (403, 429, 500, 502, 503) and attempt < tries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if attempt == tries - 1:
                print(f"  warning: skipped {url} {params.get('q', '')} ({e.__class__.__name__}: {e})")
                return None
            time.sleep(3 * (attempt + 1))
    return None


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    return s


def bluesky_posts(hashtags: Iterable[str], limit: int = 50, pause: float = 1.0,
                  session: requests.Session | None = None) -> list[Post]:
    s = session or _session()
    out: list[Post] = []
    for tag in hashtags:
        tag = tag.lstrip("#").lower()
        for sort in ("top", "latest"):
            data = _get_json(s, "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts",
                             {"q": f"#{tag}", "limit": min(limit, 100), "sort": sort})
            for p in (data or {}).get("posts", []):
                rec = p.get("record", {})
                text = rec.get("text", "")
                # Bluesky stores hashtags as "facets"; add them so captions without "#" still count.
                facet_tags = [f.get("tag", "") for fc in rec.get("facets", []) or []
                              for f in fc.get("features", []) if f.get("$type", "").endswith("#tag")]
                caption = text + " " + " ".join(f"#{t}" for t in facet_tags if t)
                handle = p.get("author", {}).get("handle", "")
                rkey = p.get("uri", "").rsplit("/", 1)[-1]
                out.append(Post(
                    id="bsky:" + p.get("uri", ""), hashtag=tag, caption=caption,
                    like_count=int(p.get("likeCount") or 0) + int(p.get("repostCount") or 0),
                    comments_count=int(p.get("replyCount") or 0),
                    timestamp=rec.get("createdAt", ""),
                    permalink=f"https://bsky.app/profile/{handle}/post/{rkey}" if handle else "",
                    source=f"bluesky-{sort}",
                ))
            time.sleep(pause)
    return out


def mastodon_posts(hashtags: Iterable[str], instance: str = "mastodon.social", limit: int = 40,
                   pause: float = 1.0, session: requests.Session | None = None) -> list[Post]:
    s = session or _session()
    out: list[Post] = []
    for tag in hashtags:
        tag = tag.lstrip("#").lower()
        data = _get_json(s, f"https://{instance}/api/v1/timelines/tag/{tag}", {"limit": min(limit, 40)})
        for st in data or []:
            text = html.unescape(TAG_RE.sub(" ", st.get("content", "")))
            caption = text + " " + " ".join(f"#{t['name']}" for t in st.get("tags", []))
            out.append(Post(
                id="masto:" + st.get("url", st.get("id", "")), hashtag=tag, caption=caption,
                like_count=int(st.get("favourites_count") or 0) + int(st.get("reblogs_count") or 0),
                comments_count=int(st.get("replies_count") or 0),
                timestamp=st.get("created_at", ""), permalink=st.get("url", ""), source="mastodon",
            ))
        time.sleep(pause)
    return out


def instagram_posts(hashtags: Iterable[str], limit: int = 50, api_version: str = "v26.0") -> list[Post]:
    client = InstagramGraphClient(access_token=os.getenv("IG_ACCESS_TOKEN", ""),
                                  ig_user_id=os.getenv("IG_USER_ID", ""), api_version=api_version)
    return client.collect(hashtags, limit=limit)


def _recent(posts: list[Post], max_age_days: float) -> list[Post]:
    """Keep posts from the last N days, so old "top" posts don't hide what's new."""
    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    keep = []
    for p in posts:
        try:
            ts = datetime.fromisoformat(p.timestamp.replace("Z", "+00:00").replace("+0000", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except (ValueError, AttributeError):
            keep.append(p)
            continue
        if ts >= cutoff:
            keep.append(p)
    return keep


def collect(sources: list[str], hashtags: list[str], cfg: dict | None = None) -> list[Post]:
    cfg = cfg or {}
    limit = int(cfg.get("rules", {}).get("posts_per_hashtag", 50))
    posts: list[Post] = []
    for src in sources:
        src = src.strip().lower()
        if src == "bluesky":
            posts += bluesky_posts(hashtags, limit=limit)
        elif src == "mastodon":
            posts += mastodon_posts(hashtags, instance=cfg.get("mastodon_instance", "mastodon.social"), limit=limit)
        elif src == "instagram":
            posts += instagram_posts(hashtags, limit=limit, api_version=cfg.get("api_version", "v26.0"))
        else:
            raise ValueError(f"Unknown source: {src} (use bluesky, mastodon, instagram)")
    seen, unique = set(), []
    for p in posts:  # same post can come back from "top" and "latest"
        if p.id not in seen:
            seen.add(p.id)
            unique.append(p)
    return _recent(unique, float(cfg.get("rules", {}).get("max_age_days", 3)))
