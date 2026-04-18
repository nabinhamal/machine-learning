import time
import os
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Watchdog")

# Configuration
API_URL = os.getenv("API_URL", "http://api:8000/health")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60")) # seconds
FAILURE_THRESHOLD = int(os.getenv("FAILURE_THRESHOLD", "3"))

def send_telegram_alert(message):
    if not BOT_TOKEN or not CHAT_ID or "your_bot_token" in BOT_TOKEN:
        logger.warning("Telegram not configured. Alert: %s", message)
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": f"🚨 <b>SYSTEM CRITICAL</b>\n\n{message}",
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logger.error("Failed to send Telegram alert: %s", e)

def monitor():
    logger.info("Starting System Watchdog monitoring %s", API_URL)
    consecutive_failures = 0
    is_down = False

    while True:
        try:
            response = requests.get(API_URL, timeout=10)
            if response.status_code == 200:
                if is_down:
                    send_telegram_alert("✅ <b>System Recovery</b>: API is back online.")
                    is_down = False
                consecutive_failures = 0
                logger.info("Health check passed.")
            else:
                consecutive_failures += 1
                logger.warning("Health check failed with status %s. Failure count: %s", response.status_code, consecutive_failures)
                
                if consecutive_failures >= FAILURE_THRESHOLD and not is_down:
                    send_telegram_alert(f"❌ <b>API Service Unhealthy</b>\nStatus: {response.status_code}\nResponse: {response.text}")
                    is_down = True
        except Exception as e:
            consecutive_failures += 1
            logger.error("Error connecting to API: %s. Failure count: %s", e, consecutive_failures)
            
            if consecutive_failures >= FAILURE_THRESHOLD and not is_down:
                send_telegram_alert(f"💀 <b>API Service Down</b>\nThe API service is unreachable.\nError: {str(e)}")
                is_down = True

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor()
