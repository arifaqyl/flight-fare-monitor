# flight-sniper

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-alert-2CA5E0?style=flat-square&logo=telegram&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-363739?style=flat-square)
![Status](https://img.shields.io/badge/status-complete-CCFF00?style=flat-square)

Polls live flight fare APIs for a target route, fires a Telegram alert the moment the price drops below a set threshold.

Built to snipe KUL→KMG (Kuala Lumpur to Kunming) direct flights for under RM800 in November 2026.

---

## How it works

```python
while True:
    price = fetch_fare(ROUTE, TARGET_DATE)   # live API call
    if price and price <= THRESHOLD:
        send_telegram(f"{ROUTE} — RM{price:.0f}")
    time.sleep(POLL_INTERVAL)                # 3h between scans
```

Randomized delays between requests to avoid rate limits. Runs as a persistent loop — background it with `nohup` or a cron job.

---

## Alert format

When a fare drops below threshold, you get:

```
✈️ KUL → KMG — RM 749
Airline: AirAsia
Duration: 4h 15m
Date: 12 Nov 2026
Book: [link]
```

## Setup

```bash
git clone https://github.com/arifaqyl/flight-sniper
cd flight-sniper
pip install requests fast-flights
```

Set your config at the top of `flight_sniper.py`:

```python
ROUTE      = "KUL-KMG"
THRESHOLD  = 800          # RM
TARGET_DATE = "2026-11"
CHAT_ID    = "your_telegram_chat_id"
BOT_TOKEN  = "your_bot_token"
POLL_INTERVAL = 10800     # 3 hours in seconds
```

## Run

```bash
python flight_sniper.py

# Or background:
nohup python flight_sniper.py &
```

## Files

| File | Purpose |
|---|---|
| `flight_sniper.py` | Main monitoring loop + Telegram alerts |
| `smart_finder.py` | Extended multi-date scan |
| `test_scrape.py` | Quick sanity check for scraping targets |

## Requirements

```
Python 3.10+
requests
fast-flights
```

---

**[arifaqyl.me](https://arifaqyl.me)** · [github.com/arifaqyl](https://github.com/arifaqyl)
