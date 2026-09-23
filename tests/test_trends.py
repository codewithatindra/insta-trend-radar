import json
from pathlib import Path

from trend_radar.cli import check_once
from trend_radar.graph_api import InstagramGraphClient, Post
from trend_radar.niches import seeds_for
from trend_radar.store import Store
from trend_radar.trends import extract_hashtags, find_trends, tag_stats

EX = Path(__file__).resolve().parent.parent / "examples"


def load(name):
    return [Post(**p) for p in json.loads((EX / name).read_text())]


def post(i, caption, likes=10):
    return Post(id=str(i), hashtag="fashion", caption=caption, like_count=likes, comments_count=0,
                timestamp="", permalink=f"https://instagram.com/p/{i}", source="recent")


def test_extract_hashtags():
    assert extract_hashtags("Love this #OOTD #StreetStyle!") == {"ootd", "streetstyle"}


def test_tag_stats_ignores_seeds_and_duplicates():
    posts = [post(1, "#fashion #barrel"), post(1, "#fashion #barrel"), post(2, "#barrel")]
    stats = tag_stats(posts, ignore={"fashion"})
    assert "fashion" not in stats
    assert stats["barrel"].posts == 2


def test_find_trends_flags_growth():
    stats = tag_stats([post(i, "#barrel") for i in range(6)] + [post(10 + i, "#style") for i in range(4)])
    trends = find_trends(stats, {"barrel": 1, "style": 4}, min_posts=3, min_growth=2.0)
    assert [t.tag for t in trends] == ["barrel"]


def test_seeds_for_presets_and_custom():
    assert "ootd" in seeds_for("fashion")
    assert seeds_for("pottery", ["#Clay"]) == ["pottery", "clay"]


def test_end_to_end_demo_data(tmp_path, capsys):
    store = Store(tmp_path / "t.sqlite")
    cfg = {"niche": "fashion", "alerts": [{"type": "console"}]}
    assert check_once(cfg, posts=load("sample_run1.json"), store=store) == []
    trends = check_once(cfg, posts=load("sample_run2.json"), store=store)
    tags = [t.tag for t in trends]
    assert "barreljeans" in tags and "chikankarilook" in tags
    assert "Trending in fashion" in capsys.readouterr().out
    # cooldown: same data again should not re-alert the same tags
    assert check_once(cfg, posts=load("sample_run2.json"), store=store) == []


class FakeResp:
    def __init__(self, data, code=200):
        self._d, self.status_code, self.content, self.text = data, code, b"x", str(data)

    def json(self):
        return self._d


class FakeSession:
    def __init__(self):
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append((url, params))
        if url.endswith("ig_hashtag_search"):
            return FakeResp({"data": [{"id": "17841"}]})
        return FakeResp({"data": [{"id": "m1", "caption": "#ootd #newtrend", "like_count": 5,
                                   "comments_count": 1, "permalink": "https://instagram.com/p/m1"}]})


def test_graph_client_calls_official_endpoints():
    s = FakeSession()
    c = InstagramGraphClient("token", "123", session=s)
    posts = c.hashtag_media("#OOTD", edge="top_media")
    assert posts[0].engagement == 6 and posts[0].source == "top"
    assert s.calls[0][0].endswith("/v26.0/ig_hashtag_search") and s.calls[0][1]["q"] == "ootd"
    assert s.calls[1][0].endswith("/17841/top_media")
