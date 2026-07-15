"""
Central configuration for the Stock Alert Bot.
Edit thresholds and sector tags here — no need to touch the screener logic files.
"""
import os

# ---------------------------------------------------------------------------
# CREDENTIALS — set these as GitHub Actions repo secrets, never hardcode here.
# Local testing: create a `.env` file (gitignored) and load with python-dotenv,
# or just export them in your shell before running.
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")       # e.g. salmathanveer17@gmail.com
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")  # 16-char app password, NOT your login password
ALERT_EMAIL_TO = os.environ.get("ALERT_EMAIL_TO", GMAIL_ADDRESS)  # where alerts land, defaults to same address

# ---------------------------------------------------------------------------
# SYSTEM A — Fundamental Accumulation Screener (runs daily, after market close)
# ---------------------------------------------------------------------------

# Only consider stocks with market cap above this (in INR). 500 crore = small-cap floor.
MIN_MARKET_CAP = 500 * 1e7  # 500 Cr

# "Near 52-week low" band — price must be within this % above the 52w low.
NEAR_52W_LOW_PCT = 10  # e.g. 10 means price <= low * 1.10

# Minimum YoY revenue/profit growth (%) to qualify. Set to None to disable a check.
MIN_YOY_REVENUE_GROWTH_PCT = 8
MIN_YOY_PROFIT_GROWTH_PCT = 8

# Dividend is a PREFERENCE, not a hard filter — flagged in output, doesn't exclude.
REQUIRE_DIVIDEND = False

# Sector tags treated as "always-in-demand / essential" — edit freely.
# These are yfinance's `sector` / `industry` string values (approximate — verify against
# actual returned values for Indian tickers, coverage varies by stock).
ESSENTIAL_SECTORS = [
    "Consumer Defensive",   # FMCG: food, household goods
    "Energy",               # Oil & gas, fuel
    "Utilities",            # Power, water
    "Healthcare",           # Pharma
    "Consumer Cyclical",    # Include cautiously — broad bucket, some non-essential names
]

# ---------------------------------------------------------------------------
# SYSTEM B — Short-Term Technical Trigger (runs every 5-15 min, market hours)
# ---------------------------------------------------------------------------

PRICE_CHANGE_TRIGGER_PCT = 3.0     # alert if abs(% change vs prev close) >= this
VOLUME_SPIKE_MULTIPLIER = 2.0      # alert if volume >= this many times the 20-day avg
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
MA_SHORT = 20
MA_LONG = 50

# Require at least this many of the 4 signals (price, volume, RSI, MA cross) to fire
# together before sending an alert — raise this to reduce noise.
MIN_SIGNALS_TO_TRIGGER = 2

# Market hours (IST) — GitHub Actions cron runs in UTC, conversion handled in workflow files.
MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"

# ---------------------------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------------------------
SHORTLIST_PATH = "data/shortlist.json"
NSE_SYMBOL_LIST_URL = (
    "https://archives.nseindia.com/content/equity/EQUITY_L.csv"
)
