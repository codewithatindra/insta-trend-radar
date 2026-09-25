# TrendPulse

**Know what India is talking about before your feed does.**

TrendPulse is an open-source, command-line trend radar for Indian creators, social media managers and small teams. Choose a niche, turn live public signals into a short India brief, or watch related hashtags for a sudden rise. It runs locally and prints to your terminal by default; Telegram, Slack/Discord webhooks and SMTP email can be configured.

[Explore the site and illustrated brief](https://codewithatindra.github.io/insta-trend-radar/) · [Run it locally](#run-it) · [Read the code](trend_radar/)

> **Demo note:** The linked GitHub Pages site is a static product page with an animated, prewritten brief. It does not fetch live trends in the browser. The Python CLI below fetches live data when you run it. The images here are screenshots of the static site, not evidence of a live dashboard or deployed backend.

![TrendPulse landing page showing the India-first proposition](docs/trendpulse-hero.png)

<details>
<summary>More views of the site</summary>

Illustrated brief (the site's scripted example, not a live feed):

![Animated sample of a finance trend brief on the site](docs/trendpulse-brief-preview.png)

Source overview:

![The site's Google Trends, YouTube, Bluesky/Mastodon and optional Instagram source cards](docs/trendpulse-sources.png)

</details>

## What works today

| Mode | Signal | Output / access |
| --- | --- | --- |
| **India Pulse** (`india`) | Public Google Trends trending-search RSS feed for India; optional YouTube Data API v3 most-popular videos chart for India. Filters topics against niche keywords, including Hindi and English presets. | An IST-stamped text brief with Google search volumes, links and an optional YouTube section. A `[NEW]` marker compares topic names with the *previous saved run*. Google needs no key; YouTube needs `YOUTUBE_API_KEY`. |
| **Hashtag radar** (`run`, `watch`) | Searches public Bluesky posts and Mastodon hashtag timelines around niche seed tags. Optional official Instagram Graph API source requires your own eligible account and Meta access. | Counts co-occurring hashtags, compares them with the previous run, and alerts if the configured minimum posts and growth threshold are met. First run builds a baseline; default growth is 2x. |
| **Offline demo** (`demo`) | Checked-in sample JSON under `examples/`. | Replays two sample runs so you can see the baseline and alert logic without network access. |

Both modes use the same local SQLite store and configured alert channels. The CLI does **not** generate post ideas, measure Instagram Reels, predict future virality, or provide a live web dashboard. Bluesky and Mastodon are global public sources, not India-only data. The Google RSS feed is public but not a guaranteed stable API; source errors are skipped with a warning.

## How it works

```text
India Pulse: Google Trends RSS (IN) + optional YouTube chart (IN)
             -> keyword filter -> compare with previous saved topics
             -> format an IST brief -> configured channels

Hashtag radar: niche seed hashtags -> Bluesky / Mastodon / optional Instagram
               -> count co-occurring tags -> compare with previous SQLite run
               -> apply minimum posts, growth and cooldown -> configured channels
```

The niches and keywords are defined in [`trend_radar/niches.py`](trend_radar/niches.py). `india.py` reads and filters the India feeds; `sources.py` collects public posts; `trends.py` scores growth; `store.py` persists runs and alert cooldowns; `alerts.py` handles output. No hosted service or scheduler is required: `watch` and `india --every` repeat while your local process is running.

## Run it

Python 3 and `pip` are required. From the repo root:

```bash
git clone https://github.com/codewithatindra/insta-trend-radar.git
cd insta-trend-radar
python -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp config.example.yaml config.yaml  # edit your niche, sources and alert channels
cp .env.example .env                 # optional: add YOUTUBE_API_KEY for YouTube

python -m trend_radar india --niche cricket
python -m trend_radar india --niche finance --every 180
python -m trend_radar run --niche fashion
python -m trend_radar watch --every 60
python -m trend_radar demo
```

The Google Trends path works without credentials. Without a YouTube key, the CLI skips YouTube and prints a note. `india --every 180` repeats at intervals of at least 30 minutes; `watch --every 60` at intervals of at least 15 minutes. Use Ctrl+C to stop. The first hashtag run only saves a baseline. For a smoke test that needs no external feeds, run `python -m trend_radar demo`; for tests, install `pytest` separately and run `pytest -q`.

The default niches include `all`, `cricket`, `bollywood`, `festivals`, `startups`, `finance`, `travel`, `food`, `fashion`, `beauty`, `fitness`, `tech` and `news` for India Pulse. Other terms act as keywords. Add custom terms to `india_keywords` in `config.yaml`.

To receive alerts beyond the console, uncomment a channel in [`config.example.yaml`](config.example.yaml) and put secrets in `.env`, not in a commit. Telegram requires a bot token and chat ID; Slack/Discord use an incoming webhook; email uses an SMTP host and credentials. Instagram is **optional**: the code uses the official Graph API, requiring your Instagram Business/Creator setup, IG user ID, access token and suitable Meta permissions. It does not scrape Instagram.

## Stack

Python CLI (`argparse`), `requests` for HTTP, PyYAML for config, `python-dotenv` for optional environment loading, standard-library `sqlite3` for history, and `pytest` tests. The site is a standalone HTML/CSS/JavaScript page served by GitHub Pages; it is separate from the CLI and has no live data connection.

## Roadmap (not shipped)

- Verify Google feed reliability and source freshness, with clearer failure and stale-data states.
- Add a hosted runner and a live, provenance-linked web view if the local brief proves useful.
- Test the briefs with Indian creators and agencies before claiming value or adding paid plans.

These are proposed next steps, not current features. Contributions and reproducible bug reports are welcome.

MIT licensed. © 2026 Atindra Mishra.
