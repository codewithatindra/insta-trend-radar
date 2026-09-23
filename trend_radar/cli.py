"""Command line entry point.

  python -m trend_radar run --niche fashion      # live check on Bluesky + Mastodon, no keys needed
  python -m trend_radar watch --every 60         # keep checking every 60 minutes
  python -m trend_radar run --source instagram   # official Instagram Graph API (needs Meta access)
  python -m trend_radar demo                     # offline demo on the sample files in examples/
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import yaml

from .alerts import build_channels, format_message
from .graph_api import Post
from .sources import collect
from .niches import seeds_for
from .store import Store
from .trends import find_trends, tag_stats

HERE = Path(__file__).resolve().parent.parent


def load_config(path: str | None) -> dict:
    if path and Path(path).exists():
        return yaml.safe_load(Path(path).read_text()) or {}
    return {}


def check_once(cfg: dict, posts: list[Post] | None = None, store: Store | None = None) -> list:
    niche = cfg.get("niche", "fashion")
    seeds = seeds_for(niche, cfg.get("hashtags"))
    rules = cfg.get("rules", {})
    store = store or Store(cfg.get("database", "data/trend_radar.sqlite"))

    if posts is None:
        sources = cfg.get("sources") or ["bluesky", "mastodon"]
        if isinstance(sources, str):
            sources = sources.split(",")
        posts = collect(sources, seeds, cfg)
        print(f"[{niche}] fetched {len(posts)} live posts from {', '.join(sources)}")

    stats = tag_stats(posts, ignore=set(seeds))
    previous = store.previous_counts(niche)
    trends = []
    if previous:  # the first run only records a baseline
        trends = find_trends(stats, previous,
                             min_posts=int(rules.get("min_posts", 3)),
                             min_growth=float(rules.get("min_growth", 2.0)),
                             top_n=int(rules.get("top_n", 10)))
        trends = [t for t in trends if not store.recently_alerted(niche, t.tag, int(rules.get("cooldown_hours", 24)))]
    store.save_run(niche, stats)

    if trends:
        text = format_message(niche, trends)
        for ch in build_channels(cfg.get("alerts")):
            ch.send(text)
        store.mark_alerted(niche, trends)
    else:
        print(f"[{niche}] no new trends this run ({len(stats)} hashtags tracked"
              + (", baseline saved" if not previous else "") + ")")
    return trends


def _load_sample(name: str) -> list[Post]:
    raw = json.loads((HERE / "examples" / name).read_text())
    return [Post(**p) for p in raw]


def demo() -> None:
    import tempfile
    db = Path(tempfile.mkdtemp()) / "demo.sqlite"
    cfg = {"niche": "fashion", "alerts": [{"type": "console"}], "database": str(db)}
    store = Store(db)
    print("OFFLINE DEMO - sample data from examples/, not live.\nRun 1 (baseline):")
    check_once(cfg, posts=_load_sample("sample_run1.json"), store=store)
    print("\nRun 2 (an hour later):")
    check_once(cfg, posts=_load_sample("sample_run2.json"), store=store)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="trend_radar", description="Instagram niche trend alerts")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo", help="offline demo with sample data")
    for name in ("run", "watch"):
        p = sub.add_parser(name)
        p.add_argument("--config", default="config.yaml")
        p.add_argument("--niche", help="override niche from config")
        p.add_argument("--source", help="comma-separated: bluesky, mastodon, instagram (default bluesky,mastodon)")
        p.add_argument("--min-growth", type=float, help="override rules.min_growth")
        if name == "watch":
            p.add_argument("--every", type=int, default=60, help="minutes between checks (default 60)")
    args = ap.parse_args(argv)

    if args.cmd == "demo":
        return demo()
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    cfg = load_config(args.config)
    if args.niche:
        cfg["niche"] = args.niche
    if args.source:
        cfg["sources"] = args.source.split(",")
    if args.min_growth:
        cfg.setdefault("rules", {})["min_growth"] = args.min_growth
    if args.cmd == "run":
        check_once(cfg)
    else:
        while True:
            check_once(cfg)
            time.sleep(max(args.every, 15) * 60)


if __name__ == "__main__":
    main()
