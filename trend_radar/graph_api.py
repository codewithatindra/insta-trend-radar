"""Small client for the official Instagram Graph API hashtag endpoints.

Docs: https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-hashtag-search
Requires an Instagram professional (Business or Creator) account linked to a
Facebook Page, plus an access token with instagram_basic permission.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable

import requests

GRAPH_URL = "https://graph.facebook.com"
MEDIA_FIELDS = "id,caption,media_type,like_count,comments_count,timestamp,permalink"


class GraphAPIError(RuntimeError):
    pass


@dataclass
class Post:
    id: str
    hashtag: str
    caption: str
    like_count: int
    comments_count: int
    timestamp: str
    permalink: str
    source: str  # "top" or "recent"

    @property
    def engagement(self) -> int:
        return (self.like_count or 0) + (self.comments_count or 0)


class InstagramGraphClient:
    def __init__(self, access_token: str, ig_user_id: str, api_version: str = "v26.0",
                 session: requests.Session | None = None, timeout: int = 20):
        if not access_token or not ig_user_id:
            raise ValueError("access_token and ig_user_id are required (see README: Setup)")
        self.access_token = access_token
        self.ig_user_id = ig_user_id
        self.base = f"{GRAPH_URL}/{api_version}"
        self.session = session or requests.Session()
        self.timeout = timeout
        self._hashtag_ids: dict[str, str] = {}

    def _get(self, path: str, params: dict) -> dict:
        params = {**params, "access_token": self.access_token}
        resp = self.session.get(f"{self.base}/{path}", params=params, timeout=self.timeout)
        data = resp.json() if resp.content else {}
        if resp.status_code != 200 or "error" in data:
            msg = data.get("error", {}).get("message", resp.text[:200])
            raise GraphAPIError(f"Graph API error on {path}: {msg}")
        return data

    def hashtag_id(self, hashtag: str) -> str:
        tag = hashtag.lstrip("#").lower()
        if tag not in self._hashtag_ids:
            data = self._get("ig_hashtag_search", {"user_id": self.ig_user_id, "q": tag})
            items = data.get("data") or []
            if not items:
                raise GraphAPIError(f"Hashtag #{tag} not found")
            self._hashtag_ids[tag] = items[0]["id"]
        return self._hashtag_ids[tag]

    def hashtag_media(self, hashtag: str, edge: str = "recent_media", limit: int = 50) -> list[Post]:
        if edge not in ("recent_media", "top_media"):
            raise ValueError("edge must be recent_media or top_media")
        tag = hashtag.lstrip("#").lower()
        hid = self.hashtag_id(tag)
        data = self._get(f"{hid}/{edge}", {"user_id": self.ig_user_id, "fields": MEDIA_FIELDS, "limit": limit})
        source = "top" if edge == "top_media" else "recent"
        return [
            Post(
                id=m.get("id", ""),
                hashtag=tag,
                caption=m.get("caption") or "",
                like_count=int(m.get("like_count") or 0),
                comments_count=int(m.get("comments_count") or 0),
                timestamp=m.get("timestamp", ""),
                permalink=m.get("permalink", ""),
                source=source,
            )
            for m in data.get("data", [])
        ]

    def collect(self, hashtags: Iterable[str], limit: int = 50, pause: float = 1.0) -> list[Post]:
        posts: list[Post] = []
        for tag in hashtags:
            for edge in ("top_media", "recent_media"):
                posts.extend(self.hashtag_media(tag, edge=edge, limit=limit))
                time.sleep(pause)
        return posts
