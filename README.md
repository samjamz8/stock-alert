# Stock Alert Bot

Two-stage NSE stock alert system:

- **System A (daily, after market close)** — scans the full NSE equity list for
  stocks near their 52-week low, with healthy YoY revenue/profit growth, in
  "always-in-demand" sectors (FMCG, Energy, Utilities, Pharma), above a
  minimum market cap. Sends a digest and saves a shortlist.
- **System B (every ~15 min, market hours)** — watches only that shortlist for
  short-term technical triggers: price spikes, volume spikes, RSI extremes,
  moving-average crossovers. Sends real-time alerts.

Both send to **Telegram** and **Email**.

## Why two stages, not one full intraday scan?

Scanning all ~2,000 NSE stocks every 15 minutes would hit yfinance's
rate limits fast. System A narrows the universe once a day (fundamentals
don't change intraday anyway); System B then watches only that shortlist
live. This also matches the intent: fundamentally sound + sector-safe
stocks, timed with a technical entry signal.

## Setup

### 1. Create a new Telegram bot
1. Open Telegram, message **@BotFather**.
2. Send `/newbot`, follow the prompts, name it e.g. `StockAlertBot`.
3. BotFather gives you a token like `123456:ABC-DEF...` — this is `TELEGRAM_BOT_TOKEN`.
4. Send any message to your new bot, then visit:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   Find `"chat":{"id": ...}` in the response — that number is `TELEGRAM_CHAT_ID`.

### 2. Create a Gmail App Password
1. Enable 2-Step Verification on the Gmail account you'll send from (if not already).
2. Go to Google Account → Security → 2-Step Verification → App passwords.
3. Generate one for "Mail" — this 16-character password is `GMAIL_APP_PASSWORD`
   (NOT your normal Gmail login password).

### 3. Add GitHub repo secrets
Repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | from step 1 |
| `TELEGRAM_CHAT_ID` | from step 1 |
| `GMAIL_ADDRESS` | your Gmail address |
| `GMAIL_APP_PASSWORD` | from step 2 |
| `ALERT_EMAIL_TO` | address to receive alerts (can be same as GMAIL_ADDRESS) |

### 3.5. Public repo? Your picks stay private, only the code is visible
This repo is safe to make **Public** — no credentials are ever hardcoded (they
all come from GitHub Secrets). Your daily shortlist (`data/shortlist.json`) is
passed between the two workflows as a **private GitHub Actions artifact**, not
committed to git, so your actual accumulation picks never appear in the
repo's public history — only the screening logic does.

### 4. Push this repo to GitHub
```bash
cd stock-alert-bot
git init
git add .
git commit -m "Initial commit: stock alert bot"
git remote add origin https://github.com/samjamz8/stock-alert-bot.git
git push -u origin main
```
GitHub Actions must have **write permission** to commit the daily shortlist:
Repo → Settings → Actions → General → Workflow permissions → "Read and write permissions".

### 5. Test manually before trusting the schedule
Repo → Actions tab → select "Daily Fundamental Screener" → "Run workflow" (manual trigger).
Check the logs, check Telegram/Email arrived, THEN let the cron schedule take over.
Do the same for "Intraday Technical Trigger" once the daily job has produced a
`data/shortlist.json`.

## Tuning

All thresholds live in `config.py` — no need to touch screener logic:
- `MIN_MARKET_CAP`, `NEAR_52W_LOW_PCT`, `MIN_YOY_REVENUE_GROWTH_PCT`, etc. for System A
- `PRICE_CHANGE_TRIGGER_PCT`, `VOLUME_SPIKE_MULTIPLIER`, `RSI_OVERBOUGHT/OVERSOLD`,
  `MIN_SIGNALS_TO_TRIGGER` for System B
- `ESSENTIAL_SECTORS` — edit this list to match your "always in demand" sector view

## Known data limitations (read before relying on this)

- **yfinance fundamental coverage is uneven for small/micro-cap NSE stocks.**
  Revenue/profit growth and sector fields are often missing for smaller names —
  these are skipped (not failed), so the shortlist skews toward large/mid-caps.
- **NSE's archive CSV can occasionally block or rate-limit** non-browser requests.
  If `run_daily.py` fails at the symbol-fetch step, retry later or lower request
  frequency in `universe.py`.
- **This is not real-time data.** Free sources carry some delay. For true
  real-time intraday data you'd need a broker API (e.g. Zerodha Kite Connect),
  which is a paid, higher-effort upgrade path if you find you need it.
- **This tool does not predict stock performance.** It mechanically applies the
  filters you specified. Nothing here is investment advice — verify shortlisted
  names yourself before acting on any alert.

## Local testing (before pushing to GitHub)

```bash
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
export GMAIL_ADDRESS="..."
export GMAIL_APP_PASSWORD="..."

pip install -r requirements.txt

# Test on a small slice first — don't scan all 2000 stocks on your first run
python3 -c "from fundamentals_screener import run_screener, save_shortlist; r = run_screener(limit=50); save_shortlist(r); print(len(r), 'matches')"

python run_intraday.py
```
