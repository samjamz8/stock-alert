"""
Entry point for the INTRADAY job (GitHub Actions: .github/workflows/intraday.yml).
Runs System B (technical trigger screener) against the shortlist produced by
the daily job, and sends alerts for anything that fires.
"""
from technical_screener import run_technical_screen
from notifier import notify


def format_alert(triggers: list[dict]) -> str:
    lines = ["⚡ <b>Intraday Triggers</b>", ""]
    for t in triggers:
        lines.append(
            f"<b>{t['symbol'].replace('.NS','')}</b> — ₹{t['price']} ({t['pct_change']:+.2f}%)\n"
            f"  {', '.join(t['signals'])}"
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
