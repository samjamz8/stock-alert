"""
Fetches the full list of NSE-listed equity symbols.

NSE publishes a master CSV of all listed equities (EQUITY_L.csv). We pull that,
then append the ".NS" suffix yfinance expects.

NOTE: NSE's archive server occasionally blocks non-browser User-Agents or
rate-limits. If this fails repeatedly, fall back to a cached copy in
data/nse_symbols_fallback.csv (checked into the repo, updated manually every
few months — NSE's listed universe doesn't change fast).
"""
import io
import csv
import requests
from config import NSE_SYMBOL_LIST_URL

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def fetch_nse_symbols(limit: int = None) -> list[str]:
    """Returns a list of yfinance-compatible tickers, e.g. ['TATAPOWER.NS', ...]."""
    resp = requests.get(NSE_SYMBOL_LIST_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    reader = csv.DictReader(io.StringIO(resp.text))
    symbols = []
    for row in reader:
        sym = row.get("SYMBOL", "").strip()
        series = row.get(" SERIES", row.get("SERIES", "")).strip()
        # "EQ" series = ordinary equity shares (excludes SME, ETFs, bonds, etc.)
        if sym and series == "EQ":
            symbols.append(f"{sym}.NS")

    if limit:
        symbols = symbols[:limit]
    return symbols


if __name__ == "__main__":
    syms = fetch_nse_symbols()
    print(f"Fetched {len(syms)} NSE equity symbols.")
    print(syms[:10])
