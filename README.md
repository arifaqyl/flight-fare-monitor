# flight-fare-monitor

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-history-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-bot-2CA5E0?style=flat-square&logo=telegram&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-363739?style=flat-square)

General-purpose flight price monitor with SQLite history tracking, trend detection, optional flight API support, and Telegram alerts.

The script scans configured routes, stores every observed price, and sends alerts when fares hit a target threshold or print a new historical low.
It is not tied to one destination. Configure the routes you care about and the monitor handles the rest.

## Features

- historical fare tracking in SQLite
- threshold alerts
- new-low alerts
- multiple route support
- optional Amadeus Flight Offers Search provider
- route configuration via `FLIGHT_ROUTES_JSON`
- Telegram bot commands: `/check`, `/history`, `/lowest`, `/routes`
- retry logic for unstable requests
- no hardcoded secrets in the public repo

## Setup

```bash
git clone https://github.com/arifaqyl/flight-fare-monitor
cd flight-fare-monitor
pip install requests fast-flights
```

Set environment variables before running:

```bash
export TG_BOT_TOKEN="your_bot_token"
export TG_CHAT_ID="your_chat_id"
# optional: prefer Amadeus over fast_flights
export FLIGHT_PROVIDER="amadeus"
export AMADEUS_CLIENT_ID="your_client_id"
export AMADEUS_CLIENT_SECRET="your_client_secret"
```

Configure routes with `FLIGHT_ROUTES_JSON` or edit the sample route inside `flight_sniper.py`.

Example:

```bash
export FLIGHT_ROUTES_JSON='[
  {"label":"KUL → SIN","from":"KUL","to":"SIN","months":[[2026,7],[2026,8]],"threshold":350,"direct":false},
  {"label":"KUL → HKG","from":"KUL","to":"HKG","months":[[2026,7]],"threshold":500,"direct":true}
]'
```

## Run

```bash
python flight_sniper.py
```

## Files

| File | Purpose |
|---|---|
| `flight_sniper.py` | main monitor loop + Telegram command handling |
| `smart_finder.py` | separate helper script for local media work |
| `test_scrape.py` | connectivity check for scraping targets |

## Security

- configure Telegram values through environment variables only
- if you use Amadeus, keep client credentials in environment variables or a local secrets file
- do not commit `.env` or local chat/token values
- if a token was ever committed previously, rotate it in Telegram BotFather

---

**[arifaqyl.me](https://arifaqyl.me)** · [github.com/arifaqyl](https://github.com/arifaqyl)
