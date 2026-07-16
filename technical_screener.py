"""
System B — Short-Term Technical Trigger Screener.

Runs frequently during market hours (every 5-15 min via GitHub Actions cron).
Only checks the shortlist produced by fundamentals_screener.py (System A) —
NOT the full NSE universe — to stay within free API rate limits.

Signals checked per stock:
  1. Price % change vs previous close  >= config.PRICE_CHANGE_TRIGGER_PCT
  2. Volume vs 20-day average volume    >= config.VOLUME_SPIKE_MULTIPLIER
  3. RSI(14) crossing overbought/oversold thresholds
  4. Short/long moving average crossover (bullish or bearish)

An alert fires when at least config.MIN_SIGNALS_TO_TRIGGER of these agree.
Each firing alert is also classified Bullish/Caution/Mixed based on which
direction the signals point, and checked against a "falling knife" guard.
"""
import json
import numpy as np
import pandas as pd
import yfinance as yf

import config


def _rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 2) if not rsi.empty else None


def load_shortlist() -> list[dict]:
    with open(config.SHORTLIST_PATH) as f:
        return json.load(f)


def _classify(pct_change, rsi, bullish_cross, bearish_cross):
    """Counts directional votes among price/RSI/MA-cross signals (volume is a
    neutral amplifier, not counted). Returns ('Bullish setup'|'Caution'|'Mixed signals', emoji)."""
    bullish_votes = 0
    bearish_votes = 0

    if pct_change > 0:
        bullish_votes += 1
    elif pct_change < 0:
        bearish_votes += 1

    if rsi is not None:
        if rsi <= config.RSI_OVERSOLD:
            bullish_votes += 1  # potential bounce off oversold
        elif rsi >= config.RSI_OVERBOUGHT:
            bearish_votes += 1  # potential pullback from overbought

    if bullish_cross:
        bullish_votes += 1
    if bearish_cross:
        bearish_votes += 1

    if bullish_votes > bearish_votes:
        return "Bullish setup", "🟢"
    elif bearish_votes > bullish_votes:
        return "Caution", "🔴"
    else:
        return "Mixed signals", "⚠️"


def check_stock(stock: dict) -> dict | None:
    """Returns a trigger dict if signals fire, else None. `stock` is a full
    shortlist entry (has symbol, sector, market_cap, pays_dividend, etc.)."""
    symbol = stock["symbol"]
    try:
        hist = yf.Ticker(symbol).history(period="3mo", interval="1d")
        if hist.empty or len(hist) < config.MA_LONG + 1:
            return None

        close = hist["Close"]
        volume = hist["Volume"]

        prev_close = close.iloc[-2]
        last_close = close.iloc[-1]
        pct_change = round(((last_close - prev_close) / prev_close) * 100, 2)

        avg_vol_20 = volume.iloc[-21:-1].mean()
        last_vol = volume.iloc[-1]
        vol_multiple = round(last_vol / avg_vol_20, 2) if avg_vol_20 else 0

        rsi = _rsi(close, config.RSI_PERIOD)

        ma_short = close.rolling(config.MA_SHORT).mean()
        ma_long = close.rolling(config.MA_LONG).mean()
        bullish_cross = ma_short.iloc[-1] > ma_long.iloc[-1] and ma_short.iloc[-2] <= ma_long.iloc[-2]
        bearish_cross = ma_short.iloc[-1] < ma_long.iloc[-1] and ma_short.iloc[-2] >= ma_long.iloc[-2]

        signals = []
        if abs(pct_change) >= config.PRICE_CHANGE_TRIGGER_PCT:
            signals.append(f"Price {pct_change:+.2f}%")
        if vol_multiple >= config.VOLUME_SPIKE_MULTIPLIER:
            signals.append(f"Volume {vol_multiple}x avg")
        if rsi is not None and (rsi >= config.RSI_OVERBOUGHT or rsi <= config.RSI_OVERSOLD):
            signals.append(f"RSI {rsi}")
        if bullish_cross:
            signals.append(f"{config.MA_SHORT}/{config.MA_LONG} DMA bullish cross")
        if bearish_cross:
            signals.append(f"{config.MA_SHORT}/{config.MA_LONG} DMA bearish cross")

        if len(signals) < config.MIN_SIGNALS_TO_TRIGGER:
            return None

        label, emoji = _classify(pct_change, rsi, bullish_cross, bearish_cross)

        # Falling-knife guard: still below its own short-term average = trend
        # hasn't turned yet, even if RSI looks "oversold".
        short_ma = close.rolling(config.SHORT_TREND_MA).mean().iloc[-1]
        still_falling = last_close < short_ma

        return {
            "symbol": symbol,
            "sector": stock.get("sector"),
            "market_cap": stock.get("market_cap"),
            "pays_dividend": stock.get("pays_dividend"),
            "pct_above_52w_low": stock.get("pct_above_52w_low"),
            "price": round(last_close, 2),
            "pct_change": pct_change,
            "signals": signals,
            "label": label,
            "emoji": emoji,
            "still_falling": still_falling,
            "stop_loss": round(last_close * (1 - config.STOP_LOSS_PCT / 100), 2),
            "target": round(last_close * (1 + config.TARGET_PROFIT_PCT / 100), 2),
        }
    except Exception:
        return None


def run_technical_screen() -> list[dict]:
    shortlist = load_shortlist()
    triggers = []
    for stock in shortlist:
        result = check_stock(stock)
        if result:
            triggers.append(result)
    return triggers


if __name__ == "__main__":
    triggers = run_technical_screen()
    print(f"{len(triggers)} triggers fired")
    for t in triggers:
        print(t)
