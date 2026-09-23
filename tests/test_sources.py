from datetime import datetime, timedelta, timezone

from trend_radar.graph_api import Post
from trend_radar.sources import _recent


def _post(pid, days_old):
    ts = (datetime.now(timezone.utc) - timedelta(days=days_old)).isoformat()
    return Post(id=pid, hashtag="x", caption="#a", like_count=1, comments_count=0,
                timestamp=ts, permalink="", source="t")


def test_recent_filter_drops_old_posts():
    kept = _recent([_post("new", 1), _post("old", 30)], max_age_days=3)
    assert [p.id for p in kept] == ["new"]
