import requests
import time
from datetime import datetime, timedelta
from fast_flights import FlightData, Passengers, get_flights

# --- 🎯 CONFIG 🎯 ---
TOKEN = "8326380455:AAGamuS5Ys3_TTrxUCeXiLDd745BWG0jw-U" # Keep this secret next time, Boss!
DREAM_PRICE = 800  # Will alert for anything RM 800 and below

def get_chat_id():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        res = requests.get(url).json()
        # Takes the ID of the last person who messaged the bot
        return res['result'][-1]['message']['chat']['id']
    except Exception as e:
        return None

def send_tg(chat_id, msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": msg})

def scan_november(chat_id):
    # Scanning Nov 1 to Nov 30, 2026
    dates = [(datetime(2026, 11, 1) + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
    print(f"\n📡 {datetime.now().strftime('%H:%M')} | Starting Mega-Scan for Nov 2026 (KUL -> KMG)...")

    for d in dates:
        print(f"🔍 Probing {d}...", end="\r")
        try:
            # Checking direct flights to Kunming
            res = get_flights(
                flight_data=[FlightData(date=d, from_airport="KUL", to_airport="KMG")],
                trip="one-way",
                fetch_mode="web"
            )

            for f in res.flights:
                if f.stops == 0: # DIRECT ONLY
                    # Extract numbers from price (e.g., 'MYR 1,200' -> 1200)
                    price = int(''.join(filter(str.isdigit, f.price)))

                    if price <= DREAM_PRICE:
                        alert = (f"🚨 TARGET HIT! RM {price} DIRECT TO KUNMING! 🚨\n"
                                f"📅 Date: {d}\n"
                                f"✈️ Airline: {f.name}\n"
                                f"⏱️ Duration: {f.duration}\n"
                                f"🚀 AIRASIA MEGA SALE MIGHT BE LIVE. GO BOOK NOW!")
                        send_tg(chat_id, alert)
                        print(f"\n🎯 FOUND! {f.name} for RM {price} on {d}")

            time.sleep(8) # Stealth delay to avoid Google blocks

        except Exception:
            continue # Skip errors (like Google blocking one date) and keep moving

if __name__ == "__main__":
    print("🚀 Initializing Operation Yunnan Sniper...")
    # 1. Wait for User to message the bot
    cid = get_chat_id()
    if not cid:
        print("❌ FAILED: I can't see you! Go to Telegram, search your bot and send it a message first.")
    else:
        print(f"✅ Connection Established! ID: {cid}")
        send_tg(cid, "🚀 Sniper Active! I am now watching ALL of November 2026 for your RM 800 Kunming ticket.")

        while True:
            scan_november(cid)
            print("\n😴 Nov Scan Complete. Resting for 3 hours to stay stealthy...")
            time.sleep(10800) # 3 hour nap so Google doesn't IP ban you
