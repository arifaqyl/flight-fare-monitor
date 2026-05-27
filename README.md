# Flight Sniper ✈️🎯

A automated flight price tracking daemon written in Python that monitors direct flights from Kuala Lumpur (KUL) to Kunming (KMG) for November 2026 and delivers instant price alerts directly to a Telegram channel/chat when prices drop to RM 800 or below.

## Features

- **Automated Monitoring**: Monitors a 30-day block in November 2026.
- **Price Threshold Alert**: Alerts immediately via Telegram when direct flights drop below the specified threshold price (RM 800).
- **Stealth Scraper Loop**: Incorporates randomized rate limits and delays (8 seconds per request, 3 hours between full scans) to run undetected by anti-scraping controls.
- **Detailed Alert Content**: Sends price, airline, duration, flight date, and booking prompts directly to your chat window.

## Project Structure

- `flight_sniper.py`: Core price monitoring and alerting script using the `fast-flights` package.
- `test_scrape.py`: Quick test utility to ensure scraping targets are accessible.

## Setup & Configuration

### Prerequisites
- Python 3.10+
- `requests`
- `fast-flights` (available via pip)

### Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/arifaqyl/flight-sniper.git
   cd flight-sniper
   ```
2. Install dependencies:
   ```bash
   pip install requests fast-flights
   ```

### Running the Monitor
1. Send a text message to your Telegram bot first so it can discover your Chat ID.
2. Launch the script:
   ```bash
   python flight_sniper.py
   ```
