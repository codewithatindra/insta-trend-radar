# Trend Radar India 🇮🇳

🌐 **TrendPulse - live site: https://codewithatindra.github.io/insta-trend-radar/**

Know what India is talking about before your feed does. Pick a niche (cricket, Bollywood, festivals, startups, finance, travel, food, fashion, tech...) and get a short brief on Telegram, Slack/Discord or email: what Indians are searching on Google, what's trending on YouTube India, and which hashtags are picking up.

Built for Indian creators, social media managers and small agencies who post on the day's trend - Diwali drops, cricket finals, IPO days, a film release, the monsoon.

```
Trend Radar India - finance | Thu 24 Sep, 09:38 AM IST

Searching on Google:
- bse [NEW] (10,000+ searches)
  NSE IPO: Stock to list today on BSE, MSEI; what GMP signals about debut gains & other details
  https://timesofindia.indiatimes.com/business/india-business/...
```

That's a real brief from the morning of 24 Sep 2026. Topics show up in English, Hindi, Telugu, Tamil and more, exactly how India searches.

## Two tools in one

| Command | What it does | Keys needed |
|---|---|---|
| `python -m trend_radar india` | **India Pulse**: today's trending Google searches in India + YouTube India trending, filtered to your niche, marked `[NEW]` when they weren't in the last brief | None for Google. Free YouTube API key for YouTube |
| `python -m trend_radar run` / `watch` | **Hashtag radar**: flags hashtags in your niche that suddenly show up 2x more than last run | None |

## Where the data comes from

| Source | What you get | Account or key? |
|---|---|---|
| **Google Trends India** | Trending searches in India right now, approx search volume, top news headline | None |
| **YouTube India** (optional) | India's most popular videos chart, views, channel, tags | Free YouTube Data API key |
| **Bluesky + Mastodon** | Live public hashtag timelines, an early global signal | None |
| **Instagram** (optional) | Official Instagram Graph API hashtag data | Business/Creator account + Meta app access |

Straight answers:
- **Instagram**: Meta has no free, keyless way to read hashtag data. The only legit route is the Graph API, which needs a Business/Creator account and Meta's App Review. This tool never logs in as you and never scrapes Instagram. What people search and watch in India is usually what lands on Reels next.
- **Google Trends**: uses Google's public "trending now" feed for India. It isn't a documented API, so Google could change it. If it fails, the run carries on with the other sources.
- **Bluesky/Mastodon** users are mostly outside India, so treat those hashtags as a global early signal, not Indian numbers.

## Quick start

```bash
git clone https://github.com/codewithatindra/insta-trend-radar.git
cd insta-trend-radar
pip install -r requirements.txt
cp config.example.yaml config.yaml
cp .env.example .env                           # add YOUTUBE_API_KEY if you want YouTube

python -m trend_radar india                    # everything trending in India right now
python -m trend_radar india --niche cricket    # only cricket
python -m trend_radar india --niche festivals --every 180   # a brief every 3 hours
```

Niches: `all`, `cricket`, `bollywood`, `festivals`, `startups`, `finance`, `travel`, `food`, `fashion`, `beauty`, `fitness`, `tech`, `news`. Anything else works as a keyword. Add your own words (brand names, cities, Hindi words) under `india_keywords` in `config.yaml`.

Hashtag radar:

```bash
python -m trend_radar run --niche bollywood    # first run saves a baseline
python -m trend_radar watch --every 60         # then check every hour
python -m trend_radar demo                     # offline demo using examples/
```

## Get a YouTube key (free, 5 minutes)

1. Open [Google Cloud Console](https://console.cloud.google.com/), create a project.
2. Enable **YouTube Data API v3**, then create an **API key**.
3. Put it in `.env` as `YOUTUBE_API_KEY=...`.

One India brief uses 1 unit of the free daily quota.

## Alerts

Set these in `config.yaml` (secrets go in `.env` as `${NAME}`):
- **Telegram**: create a bot with @BotFather, then set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`. Works well for a team group.
- **Slack / Discord**: any incoming webhook URL (`key: text` for Slack, `key: content` for Discord).
- **Email**: any SMTP server (for Gmail, use an app password).
- **Console**: prints to the terminal (default).

Times in the brief are in IST.

## Optional: add Instagram

You need an Instagram **Business or Creator** account linked to a Facebook Page, a Meta developer app with Instagram Graph API access, your IG user ID and an access token. Put `IG_USER_ID` and `IG_ACCESS_TOKEN` in `.env`, then:

```bash
python -m trend_radar run --source bluesky,mastodon,instagram
```

Instagram lets one account query **30 unique hashtags per rolling 7 days**, so keep seed lists short.

## Project layout

```
trend_radar/
  india.py       # India Pulse: Google Trends India, YouTube India, niche matching, brief
  sources.py     # hashtag sources: Bluesky, Mastodon, Instagram (optional)
  graph_api.py   # official Instagram Graph API client
  trends.py      # hashtag counting + growth detection
  store.py       # SQLite history and alert cooldowns
  alerts.py      # console, Telegram, webhook, email
  niches.py      # seed hashtags + India keywords per niche
  cli.py         # india / demo / run / watch commands
examples/        # offline files for the demo command
tests/           # pytest tests (run: pytest -q)
```

## License

MIT © 2026 Atindra Mishra. Built by @codewithatindra.
