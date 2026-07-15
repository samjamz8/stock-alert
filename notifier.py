"""
Sends alerts to Telegram and Email. Both are best-effort — if one channel
fails (bad credentials, network hiccup), the other still gets attempted and
the run doesn't crash.
"""
import smtplib
from email.mime.text import MIMEText
import requests

import config


def send_telegram(message: str) -> bool:
    if not (config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID):
        print("Telegram not configured, skipping.")
        return False
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(
            url,
            json={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"Telegram send failed: {e}")
        return False


def send_email(subject: str, body: str) -> bool:
    if not (config.GMAIL_ADDRESS and config.GMAIL_APP_PASSWORD):
        print("Email not configured, skipping.")
        return False
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = config.GMAIL_ADDRESS
        msg["To"] = config.ALERT_EMAIL_TO

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD)
            server.sendmail(config.GMAIL_ADDRESS, [config.ALERT_EMAIL_TO], msg.as_string())
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False


def notify(subject: str, message: str):
    """Sends to both channels; logs which succeeded."""
    tg_ok = send_telegram(message)
    email_ok = send_email(subject, message)
    print(f"Notify complete — Telegram: {tg_ok}, Email: {email_ok}")
