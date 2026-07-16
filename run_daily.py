"""
Entry point for the DAILY job (GitHub Actions: .github/workflows/daily.yml).
Runs System A (fundamental accumulation screener) across the full NSE
universe, saves the shortlist for System B to consume, and sends a digest.
"""
import datetime
from fundamentals_screener import run_screener, save_shortlist
from notifier import notify


def _format_cr(value_cr):
    """Formats a crore-rupee figure using Indian lakh/crore notation."""
    if value_cr is None:
        return "N/A"
    if value_cr >= 100000:
        return f"₹{value_cr / 100000:.2f}L Cr"
    return f"₹{value_cr:,.0f} Cr"


def _format_price(value):
    return f"₹{value:,.2f}" if value is not None else "N/A"


def format_digest(results: list[dict]) -> str:
    today = datetime.date.today().strftime("%d %b %Y")
    if not results:
        return f"📊 Accumulation Candidates – {today}\nNo stocks matched today's criteria."

    lines = [f"📊 <b>Accumulation Candidates – {today}</b>", ""]
    for i, r in enumerate(results[:30], start=1):  # cap message length
        div = "Y" if r["pays_dividend"] else "N"
        mcap_cr = round(r["market_cap"] / 1e7, 1) if r.get("market_cap") else None
        rev = f"{r['revenue_growth_yoy_pct']}%" if r["revenue_growth_yoy_pct"] is not None else "N/A"
        profit = f"{r['profit_growth_yoy_pct']}%" if r["profit_growth_yoy_pct"] is not None else "N/A"
        rev_abs = _format_cr(r.get("revenue_cr"))
        profit_abs = _format_cr(r.get("profit_cr"))

        lines.append(
            f"{i}. <b>{r['symbol'].replace('.NS','')}</b> "
            f"{_format_price(r['price'])} (52w low {_format_price(r['low_52w'])}, +{r['pct_above_52w_low']}%) | "
            f"MCap {_format_cr(mcap_cr)} | "
            f"Rev {rev} ({rev_abs}) | PAT {profit} ({profit_abs}) | "
            f"Div: {div} | {r['sector']}"
        )
    if len(results) > 30:
        lines.append(f"\n...and {len(results) - 30} more in the full shortlist file.")
    return "\n".join(lines)


if __name__ == "__main__":
    print("Running System A — fundamental screener over full NSE universe...")
    results = run_screener()
    save_shortlist(results)
    print(f"Found {len(results)} matches. Sending digest...")

    digest = format_digest(results)
    notify(subject="Daily Stock Accumulation Shortlist", message=digest)
