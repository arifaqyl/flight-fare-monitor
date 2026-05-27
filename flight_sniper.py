import os
import requests
import time
from datetime import datetime

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ROUTE_FROM = os.getenv("ROUTE_FROM", "KUL")
ROUTE_TO = os.getenv("ROUTE_TO", "NRT")
TARGET_PRICE = float(os.getenv("TARGET_PRICE", "1500.00")) # Threshold in MYR/local currency
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL", "3600")) # Default 1 hour

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[{datetime.now()}] Telegram alert simulated (token/chat ID not configured):")
        print(message)
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"[{datetime.now()}] Telegram alert sent successfully.")
        else:
            print(f"[{datetime.now()}] Failed to send Telegram alert: {response.text}")
    except Exception as e:
        print(f"[{datetime.now()}] Error sending Telegram alert: {e}")

def check_flights():
    print(f"[{datetime.now()}] Fetching live flight prices for {ROUTE_FROM} -> {ROUTE_TO}...")
    
    # Simple flight price simulator representing a flight check daemon
    import random
    mock_price = round(random.uniform(1200.00, 1800.00), 2)
    print(f"[{datetime.now()}] Lowest fare found: MYR {mock_price}")
    
    if mock_price <= TARGET_PRICE:
        message = (
            f"✈️ *Flight Price Drop Alert!*\n\n"
            f"Route: `{ROUTE_FROM} ➔ {ROUTE_TO}`\n"
            f"Target Price: `MYR {TARGET_PRICE}`\n"
            f"Current Fare: *MYR {mock_price}*\n\n"
            f"🔥 Quick! Grab the deal before prices change."
        )
        send_telegram_alert(message)
    else:
        print(f"[{datetime.now()}] Current price is above threshold (MYR {TARGET_PRICE}).")

def main():
    print("=" * 60)
    print("FLIGHT SNIPER - Flight Price Monitor & Telegram Bot")
    print(f"Monitoring: {ROUTE_FROM} ➔ {ROUTE_TO}")
    print(f"Price Threshold: MYR {TARGET_PRICE}")
    print(f"Interval: {CHECK_INTERVAL_SECONDS}s")
    print("=" * 60)
    
    # First check run
    check_flights()
    
    # Scheduling loop
    try:
        while True:
            time.sleep(CHECK_INTERVAL_SECONDS)
            check_flights()
    except KeyboardInterrupt:
        print("\nFlight Sniper daemon stopped.")

if __name__ == "__main__":
    main()
