# Insta Trend Radar

Give it a niche (fashion, travel, fitness, food, anything). It watches Instagram hashtags in that niche and alerts you on Telegram, Slack/Discord, or email when a hashtag suddenly starts showing up much more than before.

```
Trending in fashion right now:
- #chikankarilook: 11 posts (new vs last run), 21,090 likes+comments
- #barreljeans: 17 posts (9.0x vs last run), 30,380 likes+comments
```

It uses the **official Instagram Graph API**, with no password scraping and no fake accounts, so it won't get your account banned.

## How it works

1. You pick a niche. Each niche has a few seed hashtags (e.g. fashion: `#fashion #ootd #streetstyle ...`), and you can add your own.
2. Every run, it pulls the top and recent public posts for those seed hashtags.
3. It counts the *other* hashtags in those posts' captions, e.g. `#barreljeans` riding along with `#ootd`.
4. It compares the counts with the previous run (stored in a local SQLite file). A hashtag that appears at least 2x more often is flagged as trending.
5. It alerts you, with a 24h cooldown so the same trend isn't sent twice.

## Try it in 30 seconds (no API keys)

```bash
git clone https://github.com/codewithatindra/insta-trend-radar.git
cd insta-trend-radar
pip install -r requirements.txt
python -m trend_radar demo
```

The demo runs on sample data in `examples/` and prints an alert.

## Setup for real data

You need:
- An Instagram **Business or Creator** account (free to switch in the Instagram app settings), linked to a Facebook Page.
- A Meta developer app with the Instagram Graph API and the `instagram_basic` permission.
- Your Instagram user ID and an access token.

Steps:
1. Create an app at https://developers.facebook.com/apps and add the Instagram product.
2. In the Graph API Explorer, generate a token with `instagram_basic` and `pages_show_list`, then exchange it for a long-lived token.
3. Get your IG user ID: `GET /me/accounts?fields=instagram_business_account`.
4. `cp .env.example .env` and fill in `IG_USER_ID` and `IG_ACCESS_TOKEN`.
5. `cp config.example.yaml config.yaml` and set your `niche` and alert channels.
6. Run it:

```bash
python -m trend_radar run            # one check (the first run just saves a baseline)
python -m trend_radar watch --every 60   # check every hour
python -m trend_radar run --niche travel # try another niche
```

## Alerts

Set these in `config.yaml` (secrets go in `.env` as `${NAME}`):
- **Telegram**: create a bot with @BotFather, then set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
- **Slack / Discord**: any incoming webhook URL (`key: text` for Slack, `key: content` for Discord).
- **Email**: any SMTP server (for Gmail, use an app password).
- **Console**: prints to the terminal (default).

## Limits to know

- Instagram lets one account query **30 unique hashtags per rolling 7 days**, so keep seed lists short.
- The API only returns public posts, and not every post. Treat results as a signal, not a full census.
- Checking every hour is plenty. Very frequent checks just burn API rate limits.

## Project layout

```
trend_radar/
  graph_api.py   # official Instagram Graph API client (hashtag search, top/recent media)
  trends.py      # hashtag counting + growth detection
  store.py       # SQLite history and alert cooldowns
  alerts.py      # console, Telegram, webhook, email
  niches.py      # starter hashtags per niche
  cli.py         # demo / run / watch commands
examples/        # sample data for the demo
tests/           # pytest tests (run: pytest -q)
```

## License

MIT © 2026 Atindra Mishra. Built by [@codewithatindra](https://github.com/codewithatindra).
