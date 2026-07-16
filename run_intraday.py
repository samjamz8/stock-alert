"""
Entry point for the INTRADAY job (GitHub Actions: .github/workflows/intraday.yml).
Runs System B (technical trigger screener) against the shortlist produced by
the daily job, and sends alerts for anything that fires.
"""
from technical_screener import run_technical_screen
from notifier import notify


def _format_cr(value):
    if value is None:
        return "N/A"
    cr = value / 1e7
    return f"₹{cr / 100000:.2f}L Cr" if cr >= 100000 else f"₹{cr:,.0f} Cr"


def format_alert(triggers: list[dict]) -> str:
    lines = ["⚡ <b>Intraday Triggers</b>", ""]
    for t in triggers:
        div = "Y" if t.get("pays_dividend") else "N"
        knife_note = " ⚠️ still below its 5-day average — may still be falling, not bottoming" if t.get("still_falling") else ""
        lines.append(
            f"{t['emoji']} <b>{t['label']}</b> — <b>{t['symbol'].replace('.NS','')}</b> "
            f"₹{t['price']:,.2f} ({t['pct_change']:+.2f}%){knife_note}\n"
            f"  Signals: {', '.join(t['signals'])}\n"
            f"  Context: {t.get('pct_above_52w_low', 'N/A')}% above 52w low | "
            f"MCap {_format_cr(t.get('market_cap'))} | Div: {div} | {t.get('sector', 'N/A')}\n"
            f"  Reference levels: Stop-loss ₹{t['stop_loss']:,.2f} | Target ₹{t['target']:,.2f} "
            f"(mechanical calc from config %, not advice)\n"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print("Running System B — technical screen over shortlist...")
    triggers = run_technical_screen()
    print(f"{len(triggers)} triggers fired.")

    if triggers:
        alert_text = format_alert(triggers)
        notify(subject=f"{len(triggers)} Stock Trigger(s) Fired", message=alert_text)
    else:
        print("No triggers — nothing sent.")
