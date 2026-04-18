import os
import httpx
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Telegram Bot configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_telegram_message(message: str, parse_mode: str = "HTML") -> bool:
    """
    Sends a message to the configured Telegram chat.
    """
    if not BOT_TOKEN or not CHAT_ID or "your_bot_token" in BOT_TOKEN:
        logger.warning("Telegram Bot Token or Chat ID not properly configured. Skipping notification.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")
        return False

async def send_error_alert(error_type: str, details: str, request_info: Optional[str] = None):
    """
    Sends a structured error alert to Telegram.
    """
    message = (
        f"🚨 <b>Backend Alert: {error_type}</b>\n\n"
        f"<b>Details:</b>\n<pre>{details}</pre>\n"
    )
    if request_info:
        message += f"\n<b>Request Info:</b>\n<pre>{request_info}</pre>"
    
    await send_telegram_message(message)

async def send_health_alert(status: str, message: str):
    """
    Sends a health/downtime alert to Telegram.
    """
    icon = "✅" if status == "healthy" else "❌"
    alert_message = (
        f"{icon} <b>System Health {status.upper()}</b>\n\n"
        f"<b>Message:</b> {message}\n"
        f"<b>Time:</b> {logging.Formatter().formatTime(logging.makeLogRecord({}), '%Y-%m-%d %H:%M:%S')}"
    )
    await send_telegram_message(alert_message)
