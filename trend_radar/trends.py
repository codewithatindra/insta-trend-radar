"""Turn raw posts into trend signals.

Idea: posts under your niche's seed hashtags also carry *other* hashtags. When one
of those co-occurring hashtags suddenly shows up much more often (or with much
more engagement) than in the previous run, it's probably starting to trend.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from .graph_api import Post

HASHTAG_RE = re.compile(r"#(\w+)", re.UNICODE)


def extract_hashtags(text: str) -> set[str]:
    return {t.lower() for t in HASHTAG_RE.findall(text or "")}


@dataclass
class TagStats:
    tag: str
    posts: int = 0
    engagement: int = 0
    example_links: list[str] = field(default_factory=list)


def tag_stats(posts: list[Post], ignore: set[str] | None = None) -> dict[str, TagStats]:
    ignore = {t.lstrip("#").lower() for t in (ignore or set())}
    seen_posts: set[str] = set()
    stats: dict[str, TagStats] = defaultdict(lambda: TagStats(tag=""))
    for p in posts:
        if p.id in seen_posts:
            continue
        seen_posts.add(p.id)
        for tag in extract_hashtags(p.caption):
            if tag in ignore:
                continue
            s = stats[tag]
            s.tag = tag
            s.posts += 1
            s.engagement += p.engagement
            if p.permalink and len(s.example_links) < 3:
                s.example_links.append(p.permalink)
    return dict(stats)


@dataclass
class Trend:
    tag: str
    posts: int
    prev_posts: int
    engagement: int
    growth: float
    score: float
    example_links: list[str]
    is_new: bool

    def summary(self) -> str:
        change = "new" if self.is_new else f"{self.growth:.1f}x"
        return f"#{self.tag}: {self.posts} posts ({change} vs last run), {self.engagement:,} likes+comments"


def find_trends(current: dict[str, TagStats], previous: dict[str, int], *, min_posts: int = 3,
                min_growth: float = 2.0, top_n: int = 10) -> list[Trend]:
    """Compare this run's tag counts with the previous run's.

    growth = (posts + 1) / (prev_posts + 1)   (the +1 keeps brand-new tags from dividing by zero)
    score  = growth * log-ish engagement weight, used only for ranking.
    """
    trends: list[Trend] = []
    for tag, s in current.items():
        if s.posts < min_posts:
            continue
        prev = previous.get(tag, 0)
        growth = (s.posts + 1) / (prev + 1)
        if growth < min_growth:
            continue
        weight = 1 + len(str(max(s.engagement, 1)))  # rough order of magnitude
        trends.append(Trend(tag=tag, posts=s.posts, prev_posts=prev, engagement=s.engagement,
                            growth=growth, score=growth * weight, example_links=s.example_links,
                            is_new=prev == 0))
    trends.sort(key=lambda t: t.score, reverse=True)
    return trends[:top_n]
