"""
flight-fare-monitor v2
Monitors flight prices for configured routes, stores history in SQLite,
sends Telegram alerts when price hits threshold or drops to a new low.
Supports on-demand /check and /history bot commands.
"""

import json
import os
import sys
import time
import sqlite3
import logging
from datetime import datetime, timedelta

import requests
from fast_flights import FlightData, get_flights

# ── CONFIG ───────────────────────────────────────────────────────────────────
# Configure via environment variables only.
BOT_TOKEN  = os.getenv("TG_BOT_TOKEN", "").strip()
CHAT_ID    = os.getenv("TG_CHAT_ID", "").strip()        # filled on first run from getUpdates
FLIGHT_PROVIDER = os.getenv("FLIGHT_PROVIDER", "auto").strip().lower()
AMADEUS_BASE_URL = os.getenv("AMADEUS_BASE_URL", "https://test.api.amadeus.com").rstrip("/")
AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID", "").strip()
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET", "").strip()
_AMADEUS_TOKEN = {"value": None, "expires_at": 0.0}

ROUTES = []

DB_PATH        = "price_history.db"
POLL_INTERVAL  = 3 * 3600    # 3 hours between full scans
REQUEST_DELAY  = 8           # seconds between individual date requests
MAX_RETRIES    = 3
RETRY_BACKOFF  = 30          # seconds before retry on failure

# ── LOGGING ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("sniper.log"),
    ]
)
log = logging.getLogger("sniper")

if not BOT_TOKEN:
    log.warning("TG_BOT_TOKEN is not set. Telegram alerts and bot commands are disabled until it is configured.")
if FLIGHT_PROVIDER == "amadeus" and not (AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET):
    log.warning("FLIGHT_PROVIDER=amadeus but Amadeus credentials are missing; the monitor will fall back to fast_flights.")

def _load_routes():
    raw = os.getenv("FLIGHT_ROUTES_JSON", "").strip()
    if raw:
        try:
            routes = json.loads(raw)
            if isinstance(routes, list) and routes:
                return [_normalize_route(route) for route in routes]
        except json.JSONDecodeError as exc:
            log.warning(f"FLIGHT_ROUTES_JSON could not be parsed: {exc}")

    next_month = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1)
    return [
        _normalize_route(
            {
                "label": "KUL → SIN (sample)",
                "from": "KUL",
                "to": "SIN",
                "months": [(next_month.year, next_month.month)],
                "threshold": 300,
                "direct": False,
            }
        )
    ]


def _normalize_route(route):
    year_months = route.get("months") or []
    months = []
    for item in year_months:
        try:
            year, month = item
            months.append((int(year), int(month)))
        except Exception:
            continue
    if not months:
        next_month = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1)
        months = [(next_month.year, next_month.month)]
    return {
        "label": route.get("label") or f"{route.get('from', 'XXX')} → {route.get('to', 'YYY')}",
        "from": str(route.get("from", "")).strip().upper(),
        "to": str(route.get("to", "")).strip().upper(),
        "months": months,
        "threshold": int(route.get("threshold", 0)),
        "direct": bool(route.get("direct", False)),
    }


ROUTES = _load_routes()

# ── DATABASE ─────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            route     TEXT    NOT NULL,
            date      TEXT    NOT NULL,
            airline   TEXT,
            price     INTEGER NOT NULL,
            duration  TEXT,
            stops     INTEGER DEFAULT 0,
            scanned   TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def record_price(conn, route_label, date, airline, price, duration, stops):
    conn.execute(
        "INSERT INTO prices (route, date, airline, price, duration, stops) VALUES (?,?,?,?,?,?)",
        (route_label, date, airline, price, duration, stops)
    )
    conn.commit()


def get_lowest_ever(conn, route_label, date=None):
    if date:
        row = conn.execute(
            "SELECT MIN(price) FROM prices WHERE route=? AND date=?",
            (route_label, date)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT MIN(price) FROM prices WHERE route=?", (route_label,)
        ).fetchone()
    return row[0] if row and row[0] else None


def get_price_history(conn, route_label, limit=14):
    rows = conn.execute(
        "SELECT date, airline, price, scanned FROM prices WHERE route=? ORDER BY scanned DESC LIMIT ?",
        (route_label, limit)
    ).fetchall()
    return rows

# ── TELEGRAM ─────────────────────────────────────────────────────────────────
def tg_send(chat_id, text):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
        return r.ok
    except Exception as e:
        log.warning(f"Telegram send failed: {e}")
        return False


def tg_get_updates(offset=None):
    try:
        params = {"timeout": 30, "allowed_updates": ["message"]}
        if offset:
            params["offset"] = offset
        r = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
            params=params, timeout=35
        )
        return r.json().get("result", [])
    except Exception:
        return []


def resolve_chat_id():
    """Wait for the user to message the bot, return their chat ID."""
    log.info("Waiting for you to message the bot on Telegram...")
    while True:
        updates = tg_get_updates()
        if updates:
            cid = updates[-1]["message"]["chat"]["id"]
            log.info(f"Chat ID found: {cid}")
            return str(cid)
        time.sleep(3)

# ── FETCH PRICES ─────────────────────────────────────────────────────────────
def fetch_prices(from_airport, to_airport, date_str, direct_only=True):
    """Fetch flight prices for a single date. Returns list of dicts."""
    providers = _provider_order()
    last_error = None
    for provider in providers:
        try:
            if provider == "amadeus":
                results = fetch_prices_amadeus(from_airport, to_airport, date_str, direct_only=direct_only)
            else:
                results = fetch_prices_fast_flights(from_airport, to_airport, date_str, direct_only=direct_only)
            if results is not None:
                return results
        except Exception as exc:
            last_error = exc
            log.warning(f"{provider} fetch failed for {from_airport}→{to_airport} {date_str}: {exc}")
    if last_error:
        log.error(f"All providers failed for {from_airport}→{to_airport} {date_str}: {last_error}")
    return []


def _provider_order():
    if FLIGHT_PROVIDER == "amadeus":
        return ["amadeus", "fast_flights"]
    if FLIGHT_PROVIDER == "fast_flights":
        return ["fast_flights"]
    if AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET:
        return ["amadeus", "fast_flights"]
    return ["fast_flights"]


def fetch_prices_fast_flights(from_airport, to_airport, date_str, direct_only=True):
    """Fetch flight prices for a single date with fast_flights. Returns list of dicts."""
    for attempt in range(MAX_RETRIES):
        try:
            res = get_flights(
                flight_data=[FlightData(date=date_str,
                                        from_airport=from_airport,
                                        to_airport=to_airport)],
                trip="one-way",
                fetch_mode="web"
            )
            results = []
            for f in res.flights:
                if direct_only and f.stops != 0:
                    continue
                try:
                    price = int(''.join(filter(str.isdigit, f.price)))
                except (ValueError, AttributeError):
                    continue
                results.append({
                    "airline":  f.name,
                    "price":    price,
                    "duration": getattr(f, "duration", ""),
                    "stops":    f.stops,
                })
            return results
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                log.warning(f"Fetch failed ({e}), retrying in {RETRY_BACKOFF}s...")
                time.sleep(RETRY_BACKOFF)
            else:
                log.error(f"All retries failed for {from_airport}→{to_airport} {date_str}: {e}")
                return []


def fetch_prices_amadeus(from_airport, to_airport, date_str, direct_only=True):
    if not (AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET):
        return None

    token = _amadeus_access_token()
    if not token:
        return None

    params = {
        "originLocationCode": from_airport,
        "destinationLocationCode": to_airport,
        "departureDate": date_str,
        "adults": 1,
        "currencyCode": "MYR",
        "max": 20,
        "nonStop": str(bool(direct_only)).lower(),
    }
    response = requests.get(
        f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers",
        params=params,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=20,
    )
    if response.status_code in {401, 403}:
        _AMADEUS_TOKEN["value"] = None
        _AMADEUS_TOKEN["expires_at"] = 0.0
        return None
    response.raise_for_status()
    payload = response.json()
    offers = payload.get("data") or []
    results = []
    for offer in offers:
        itinerary = (offer.get("itineraries") or [{}])[0]
        segments = itinerary.get("segments") or []
        stops = max(len(segments) - 1, 0)
        if direct_only and stops != 0:
            continue
        price_obj = offer.get("price") or {}
        price_raw = price_obj.get("grandTotal") or price_obj.get("total")
        try:
            price = int(float(price_raw))
        except (TypeError, ValueError):
            continue
        airline = _amadeus_airline_name(offer) or "Unknown"
        duration = itinerary.get("duration", "")
        results.append({
            "airline": airline,
            "price": price,
            "duration": duration,
            "stops": stops,
        })
    return results


def _amadeus_access_token():
    now = time.time()
    if _AMADEUS_TOKEN["value"] and _AMADEUS_TOKEN["expires_at"] > now + 60:
        return _AMADEUS_TOKEN["value"]

    response = requests.post(
        f"{AMADEUS_BASE_URL}/v1/security/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": AMADEUS_CLIENT_ID,
            "client_secret": AMADEUS_CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("access_token")
    expires_in = int(payload.get("expires_in", 1800))
    if not token:
        return None
    _AMADEUS_TOKEN["value"] = token
    _AMADEUS_TOKEN["expires_at"] = now + expires_in
    return token


def _amadeus_airline_name(offer):
    codes = offer.get("validatingAirlineCodes") or []
    if codes:
        return codes[0]
    segments = ((offer.get("itineraries") or [{}])[0].get("segments") or [])
    for segment in segments:
        carrier = segment.get("carrierCode")
        if carrier:
            return carrier
    return ""

# ── SCAN ─────────────────────────────────────────────────────────────────────
def scan_route(conn, route, chat_id):
    label     = route["label"]
    fr        = route["from"]
    to        = route["to"]
    threshold = route["threshold"]
    direct    = route["direct"]
    months    = route["months"]

    dates = []
    for year, month in months:
        # Build all dates in the month
        d = datetime(year, month, 1)
        while d.month == month:
            dates.append(d.strftime("%Y-%m-%d"))
            d += timedelta(days=1)

    log.info(f"Scanning {label} — {len(dates)} dates")

    for date_str in dates:
        results = fetch_prices(fr, to, date_str, direct_only=direct)

        for r in results:
            price = r["price"]
            record_price(conn, label, date_str, r["airline"], price, r["duration"], r["stops"])

            prev_low = get_lowest_ever(conn, label, date_str)
            is_new_low = prev_low is None or price < prev_low

            if price <= threshold:
                stops_tag = "direct" if r["stops"] == 0 else f"{r['stops']} stop"
                msg = (
                    f"<b>TARGET HIT — {label}</b>\n"
                    f"RM {price} · {r['airline']} · {stops_tag}\n"
                    f"Date: {date_str}  |  Duration: {r['duration']}\n"
                )
                if is_new_low:
                    msg += f"<b>NEW HISTORICAL LOW</b> (prev: RM {prev_low})\n"
                msg += f"Book now before it goes up."
                tg_send(chat_id, msg)
                log.info(f"ALERT: {label} {date_str} RM {price}")

            elif is_new_low and prev_low is not None and price < prev_low * 0.9:
                tg_send(chat_id,
                    f"{label}: new low RM {price} on {date_str} "
                    f"(was RM {prev_low}) — still above threshold"
                )

        time.sleep(REQUEST_DELAY)

# ── BOT COMMAND HANDLER ───────────────────────────────────────────────────────
def handle_commands(conn, chat_id, last_update_id):
    """Process any pending Telegram commands. Returns new offset."""
    updates = tg_get_updates(offset=last_update_id + 1 if last_update_id else None)
    for upd in updates:
        last_update_id = upd["update_id"]
        msg = upd.get("message", {})
        text = msg.get("text", "").strip()

        if text.startswith("/check"):
            tg_send(chat_id, "Scanning now...")
            for route in ROUTES:
                scan_route(conn, route, chat_id)
            tg_send(chat_id, "Scan complete.")

        elif text.startswith("/history"):
            parts = text.split(maxsplit=1)
            route_label = parts[1] if len(parts) > 1 else ROUTES[0]["label"]
            rows = get_price_history(conn, route_label)
            if not rows:
                tg_send(chat_id, f"No history for {route_label}")
            else:
                lines = [f"<b>Last {len(rows)} checks — {route_label}</b>"]
                for date, airline, price, scanned in rows:
                    lines.append(f"RM {price}  {date}  {airline}  ({scanned[:10]})")
                tg_send(chat_id, "\n".join(lines))

        elif text.startswith("/lowest"):
            lines = ["<b>Historical lows per route</b>"]
            for route in ROUTES:
                low = get_lowest_ever(conn, route["label"])
                lines.append(f"{route['label']}: RM {low if low else 'no data'}")
            tg_send(chat_id, "\n".join(lines))

        elif text.startswith("/routes"):
            lines = ["<b>Watching</b>"]
            for r in ROUTES:
                months_str = ", ".join(f"{m[0]}-{m[1]:02d}" for m in r["months"])
                lines.append(f"{r['label']} | threshold RM {r['threshold']} | {months_str}")
            tg_send(chat_id, "\n".join(lines))

        elif text.startswith("/help") or text.startswith("/start"):
            tg_send(chat_id,
                "<b>flight-fare-monitor commands</b>\n"
                "/check — scan all routes now\n"
                "/history [route] — last 14 price records\n"
                "/lowest — historical low per route\n"
                "/routes — show configured routes\n"
                "/help — this message"
            )

    return last_update_id

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    conn = init_db()
    log.info("flight-fare-monitor v2 starting")

    chat_id = CHAT_ID
    if not chat_id:
        chat_id = resolve_chat_id()

    tg_send(chat_id,
        "<b>flight-fare-monitor v2 active</b>\n"
        + "\n".join(
            f"{r['label']} — alert at ≤ RM {r['threshold']}"
            for r in ROUTES
        )
        + "\n\nSend /help for commands."
    )

    last_update_id = None

    while True:
        # Check for bot commands first
        last_update_id = handle_commands(conn, chat_id, last_update_id)

        # Run scheduled full scan
        log.info("Starting scheduled scan...")
        for route in ROUTES:
            scan_route(conn, route, chat_id)

        log.info(f"Scan complete. Sleeping {POLL_INTERVAL // 3600}h...")
        tg_send(chat_id, f"Scan complete. Next check in {POLL_INTERVAL // 3600}h.")

        # Sleep in 30s chunks so commands are handled during the sleep window
        elapsed = 0
        while elapsed < POLL_INTERVAL:
            time.sleep(30)
            elapsed += 30
            last_update_id = handle_commands(conn, chat_id, last_update_id)


if __name__ == "__main__":
    main()
