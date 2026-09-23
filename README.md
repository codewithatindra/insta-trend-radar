# Insta Trend Radar

Give it a niche (fashion, travel, fitness, food, anything). It watches hashtags in that niche on live social feeds and alerts you on Telegram, Slack/Discord, or email when a hashtag suddenly starts showing up much more than before.

```
Trending in travel right now:
- #worldgratitudeday: 3 posts (new vs last run), 0 likes+comments
  e.g. https://bsky.app/profile/earthchangers.bsky.social/post/3mvzzz7xcxi2l
- #tajmahal: 2 posts (new vs last run), 0 likes+comments
```

## Where the data comes from

| Source | Real data? | Account or key needed? |
|---|---|---|
| **Bluesky** (default) | Yes, live public posts via the official public API | None |
| **Mastodon** (default) | Yes, live public hashtag timelines via the official API | None |
| **Instagram** (optional) | Yes, via the official Instagram Graph API | Instagram Business/Creator account + Meta app access |

Straight answer on Instagram: Meta does not offer a free, keyless way to read Instagram hashtag data. The only legit route is the Graph API, which needs a Business/Creator account and app access. This tool never logs in as you and never scrapes Instagram pages.

So by default it runs on Bluesky + Mastodon, which are open and free, and hashtags that pick up there (fashion, travel, food, tech) are a good early signal for what will show up on Instagram. If you have Meta access, add Instagram as a source.

## How it works

1. You pick a niche. Each niche has a few seed hashtags (e.g. fashion: `#fashion #ootd #streetstyle ...`), and you can add your own.
2. Every run, it pulls top and latest public posts for those seed hashtags from the last 3 days.
3. It counts the *other* hashtags in those posts, e.g. `#barreljeans` riding along with `#ootd`.
4. It compares the counts with the previous run (stored in a local SQLite file). A hashtag that appears at least 2x more often is flagged as trending.
5. It alerts you, with a 24h cooldown so the same trend isn't sent twice.

## Quick start (live data, no keys)

```bash
git clone https://github.com/codewithatindra/insta-trend-radar.git
cd insta-trend-radar
pip install -r requirements.txt
cp config.example.yaml config.yaml
python -m trend_radar run --niche travel      # first run saves a baseline
python -m trend_radar watch --every 60        # then check every hour
```

`python -m trend_radar demo` still exists for trying the alert format offline; it uses the files in `examples/` and says so when it runs.

## Optional: add Instagram

You need an Instagram **Business or Creator** account linked to a Facebook Page, a Meta developer app with the Instagram Graph API (`instagram_basic`), your IG user ID, and an access token. Put `IG_USER_ID` and `IG_ACCESS_TOKEN` in `.env`, then:

```bash
python -m trend_radar run --source bluesky,mastodon,instagram
```

Instagram lets one account query **30 unique hashtags per rolling 7 days**, so keep seed lists short when Instagram is on.

## Alerts

Set these in `config.yaml` (secrets go in `.env` as `${NAME}`):
- **Telegram**: create a bot with @BotFather, then set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
- **Slack / Discord**: any incoming webhook URL (`key: text` for Slack, `key: content` for Discord).
- **Email**: any SMTP server (for Gmail, use an app password).
- **Console**: prints to the terminal (default).

## Limits to know

- Every source returns only public posts, and not every post. Treat results as a signal, not a full census.
- Bluesky and Mastodon trends lead or echo Instagram trends; they are not Instagram numbers.
- Checking every hour is plenty. Very frequent checks just hit rate limits.

## Project layout

```
trend_radar/
  sources.py     # live sources: Bluesky, Mastodon, Instagram (optional)
  graph_api.py   # official Instagram Graph API client (hashtag search, top/recent media)
  trends.py      # hashtag counting + growth detection
  store.py       # SQLite history and alert cooldowns
  alerts.py      # console, Telegram, webhook, email
  niches.py      # starter hashtags per niche
  cli.py         # demo / run / watch commands
examples/        # offline files for the demo command
tests/           # pytest tests (run: pytest -q)
```

## License

MIT © 2026 Atindra Mishra. Built by [@codewithatindra](https://github.com/codewithatindra).
