"""
Entry point for the DAILY job (GitHub Actions: .github/workflows/daily.yml).
Runs System A (fundamental accumulation screener) across the full NSE
universe, saves the shortlist for System B to consume, and sends a digest.
"""
import datetime
from fundamentals_screener import run_screener, save_shortlist
from notifier import notify


def format_digest(results: list[dict]) -> str:
    today = datetime.date.today().strftime("%d %b %Y")
    if not results:
        return f"📊 Accumulation Candidates – {today}\nNo stocks matched today's criteria."

    lines = [f"📊 <b>Accumulation Candidates – {today}</b>", ""]
    for i, r in enumerate(results[:30], start=1):  # cap message length
        div = "Yes" if r["pays_dividend"] else "No"
        rev = f"{r['revenue_growth_yoy_pct']}%" if r["revenue_growth_yoy_pct"] is not None else "N/A"
        profit = f"{r['profit_growth_yoy_pct']}%" if r["profit_growth_yoy_pct"] is not None else "N/A"
        lines.append(
            f"{i}. <b>{r['symbol'].replace('.NS','')}</b> — "
            f"{r['pct_above_52w_low']}% above 52w low | "
            f"Rev YoY {rev} | Profit YoY {profit} | Div: {div} | {r['sector']}"
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
