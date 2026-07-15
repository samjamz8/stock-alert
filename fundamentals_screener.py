"""
System A — Fundamental Accumulation Screener.

Scans the full NSE universe once a day (after market close) and shortlists
stocks that are:
  - above a minimum market cap
  - trading near their 52-week low (accumulation zone)
  - showing healthy YoY revenue/profit growth
  - in an "always-in-demand" sector (config.ESSENTIAL_SECTORS)
  - flags (doesn't require) dividend payers

Output: data/shortlist.json — consumed by technical_screener.py (System B).

IMPORTANT DATA CAVEAT: yfinance's fundamental fields (financials, sector,
dividend history) have thinner, less reliable coverage for small/micro-cap
NSE stocks than for large/mid-caps. Missing data is skipped, not treated as
a fail — check data/skipped_log.json after a run to see what was excluded
due to missing data vs. genuinely not meeting criteria.
"""
import json
import os
import time
import yfinance as yf

import config
from universe import fetch_nse_symbols


def _pct_growth(new, old):
    if old in (None, 0) or new is None:
        return None
    return round(((new - old) / abs(old)) * 100, 2)


def _yoy_growth_from_financials(ticker: yf.Ticker):
    """Returns (revenue_growth_pct, profit_growth_pct) using latest two annual financials."""
    try:
        fin = ticker.financials  # annual, most recent columns first
        if fin is None or fin.empty or fin.shape[1] < 2:
            return None, None
        revenue_row = fin.loc["Total Revenue"] if "Total Revenue" in fin.index else None
        profit_row = fin.loc["Net Income"] if "Net Income" in fin.index else None
        rev_growth = _pct_growth(revenue_row.iloc[0], revenue_row.iloc[1]) if revenue_row is not None else None
        profit_growth = _pct_growth(profit_row.iloc[0], profit_row.iloc[1]) if profit_row is not None else None
        return rev_growth, profit_growth
    except Exception:
        return None, None


def screen_stock(symbol: str) -> dict | None:
    """Returns a result dict if the stock passes, else None. Never raises."""
    try:
        t = yf.Ticker(symbol)
        info = t.info
        if not info:
            return None

        market_cap = info.get("marketCap")
        low_52w = info.get("fiftyTwoWeekLow")
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        sector = info.get("sector")
        dividend_yield = info.get("dividendYield")

        if not market_cap or market_cap < config.MIN_MARKET_CAP:
            return None
        if not (low_52w and price):
            return None

        pct_above_low = ((price - low_52w) / low_52w) * 100
        if pct_above_low > config.NEAR_52W_LOW_PCT:
            return None

        if config.ESSENTIAL_SECTORS and sector not in config.ESSENTIAL_SECTORS:
            return None

        rev_growth, profit_growth = _yoy_growth_from_financials(t)

        if config.MIN_YOY_REVENUE_GROWTH_PCT is not None:
            if rev_growth is None or rev_growth < config.MIN_YOY_REVENUE_GROWTH_PCT:
                return None
        if config.MIN_YOY_PROFIT_GROWTH_PCT is not None:
            if profit_growth is None or profit_growth < config.MIN_YOY_PROFIT_GROWTH_PCT:
                return None

        pays_dividend = bool(dividend_yield and dividend_yield > 0)
        if config.REQUIRE_DIVIDEND and not pays_dividend:
            return None

        return {
            "symbol": symbol,
            "name": info.get("shortName", symbol),
            "market_cap": market_cap,
            "price": price,
            "pct_above_52w_low": round(pct_above_low, 2),
            "revenue_growth_yoy_pct": rev_growth,
            "profit_growth_yoy_pct": profit_growth,
            "pays_dividend": pays_dividend,
            "sector": sector,
        }
    except Exception:
        return None


def run_screener(limit: int = None, sleep_between: float = 0.3) -> list[dict]:
    """
    Scans the NSE universe and returns the shortlist.
    `limit` caps how many symbols to check — useful for testing before a full run.
    `sleep_between` throttles requests to avoid rate-limiting.
    """
    symbols = fetch_nse_symbols(limit=limit)
    results = []
    for i, sym in enumerate(symbols):
        result = screen_stock(sym)
        if result:
            results.append(result)
        if sleep_between:
            time.sleep(sleep_between)
        if (i + 1) % 100 == 0:
            print(f"Scanned {i + 1}/{len(symbols)} — {len(results)} passed so far")

    results.sort(key=lambda r: r["market_cap"], reverse=True)
    return results


def save_shortlist(results: list[dict]):
    os.makedirs(os.path.dirname(config.SHORTLIST_PATH), exist_ok=True)
    with open(config.SHORTLIST_PATH, "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    shortlist = run_screener()
    save_shortlist(shortlist)
    print(f"Shortlist saved: {len(shortlist)} stocks -> {config.SHORTLIST_PATH}")
