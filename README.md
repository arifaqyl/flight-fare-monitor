# flight-sniper

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-history-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-bot-2CA5E0?style=flat-square&logo=telegram&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-363739?style=flat-square)
![Version](https://img.shields.io/badge/version-2.0-CCFF00?style=flat-square)

Persistent flight price monitor with SQLite history tracking, trend detection, and a Telegram bot interface.

Scans configured routes every 3 hours, stores every price check in a local database, and alerts you when fares hit your threshold or drop to a new historical low.

---

## What's new in v2

- **Price history** — every checked fare is stored in `price_history.db` with timestamp
- **Trend detection** — alerts when a price is both at threshold AND a new historical low
- **Multi-route** — add as many `ROUTES` entries as you want in the config
- **Bot commands** — `/check`, `/history`, `/lowest`, `/routes` via Telegram
- **Retry logic** — exponential backoff when requests fail
- **No hardcoded secrets** — reads `TG_BOT_TOKEN` and `TG_CHAT_ID` from env vars

---

## How it works

```
[scheduled scan — every 3h]
  for each route → for each date → fetch_prices()
    → record to SQLite
    → if price <= threshold → Telegram alert
    → if new historical low → Telegram alert
  sleep (handles /check commands during sleep window)
```

## Bot commands

| Command | Action |
|---|---|
| `/check` | Scan all routes immediately |
| `/history [route]` | Last 14 price records for a route |
| `/lowest` | Historical low per route |
| `/routes` | Show configured routes + thresholds |
| `/help` | Command list |

## Setup

```bash
git clone https://github.com/arifaqyl/flight-sniper
cd flight-sniper
pip install requests fast-flights
```

Set env vars (or edit config dict at top of `flight_sniper.py`):

```bash
export TG_BOT_TOKEN="your_bot_token"
export TG_CHAT_ID="your_chat_id"
```

Configure routes in `ROUTES` list:

```python
ROUTES = [
    {
        "label":     "KUL → KMG (Yunnan)",
        "from":      "KUL",
        "to":        "KMG",
        "months":    [(2026, 11)],
        "threshold": 800,
        "direct":    True,
    },
]
```

## Run

```bash
python flight_sniper.py

# Background:
nohup python flight_sniper.py &
```

## Files

| File | Purpose |
|---|---|
| `flight_sniper.py` | Main daemon — scan loop + Telegram bot |
| `smart_finder.py` | Whisper-based hype-moment finder (local video) |
| `test_scrape.py` | Connectivity check for scraping targets |
| `price_history.db` | SQLite — auto-created on first run |
| `sniper.log` | Persistent run log |

## Requirements

```
Python 3.10+
requests
fast-flights
```

---

**[arifaqyl.me](https://arifaqyl.me)** · [github.com/arifaqyl](https://github.com/arifaqyl)
