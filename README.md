# Flight Sniper ✈️🎯

A automated flight price tracking daemon written in Python that monitors target flight routes and delivers instant alert notifications directly to a Telegram channel/chat when prices fall below a specified threshold.

## Features

- **Automated Monitoring**: Daemon process checks flight prices at configurable intervals (e.g., hourly, daily).
- **Price Drop Alerts**: Compares current lowest fares against a target budget price threshold.
- **Telegram Notifications**: Direct message alerts containing route info, current lowest price, and quick action prompts via the Telegram Bot API.
- **Robust Daemon Loop**: Continuous execution loop designed to run 24/7 on a cloud host/server (e.g., DigitalOcean via PM2).

## Project Structure

- `flight_sniper.py`: Core price checker daemon script.
- `test_scrape.py`: Quick verification script to test connectivity to search platforms (Google Flights, Skyscanner).

## Setup & Configuration

### Prerequisites
- Python 3.10+
- `requests` library

### Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/arifaqyl/flight-sniper.git
   cd flight-sniper
   ```
2. Install dependencies:
   ```bash
   pip install requests
   ```

### Configuration
Set the following environment variables or customize them within the script:
- `TELEGRAM_BOT_TOKEN`: The API token of your Telegram bot (created via BotFather).
- `TELEGRAM_CHAT_ID`: The Telegram chat or channel ID to receive alerts.
- `ROUTE_FROM`: Origin airport IATA code (e.g., `KUL` for Kuala Lumpur).
- `ROUTE_TO`: Destination airport IATA code (e.g., `NRT` for Tokyo Narita).
- `TARGET_PRICE`: Budget threshold (e.g., `1500.00`).
- `CHECK_INTERVAL`: Monitoring frequency in seconds (default: `3600`).

### Running the Monitor
Run the daemon manually:
```bash
python flight_sniper.py
```

To run continuously in the background on Linux/server:
```bash
pm2 start flight_sniper.py --name "flight-sniper" --interpreter python3
```

## License
MIT
