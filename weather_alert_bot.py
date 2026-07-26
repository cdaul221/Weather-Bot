"""Weather Alert Bot.

Checks tomorrow's forecast for a fixed location via the Open-Meteo API and
posts a Discord alert only if rain, snow, or extreme temperatures are
expected. Sends nothing when conditions are unremarkable.
"""

import os
import sys
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

# Location: Chicago, IL. Change these to point the bot elsewhere.
LATITUDE = 41.8781
LONGITUDE = -87.6298
LOCATION_NAME = "Chicago, IL"
TIMEZONE = "America/Chicago"

# Alert thresholds.
RAIN_PROBABILITY_THRESHOLD = 50  # percent
SNOW_THRESHOLD_CM = 0  # any measurable snowfall
EXTREME_COLD_F = 20
EXTREME_HOT_F = 95

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_tomorrows_forecast():
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "daily": [
            "precipitation_probability_max",
            "snowfall_sum",
            "temperature_2m_max",
            "temperature_2m_min",
        ],
        "temperature_unit": "fahrenheit",
        "timezone": TIMEZONE,
        "forecast_days": 3,
    }
    response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
    response.raise_for_status()
    daily = response.json()["daily"]

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    if tomorrow not in daily["time"]:
        raise ValueError(f"Tomorrow ({tomorrow}) not found in forecast response")
    idx = daily["time"].index(tomorrow)

    return {
        "date": daily["time"][idx],
        "rain_probability": daily["precipitation_probability_max"][idx],
        "snowfall_cm": daily["snowfall_sum"][idx],
        "temp_max_f": daily["temperature_2m_max"][idx],
        "temp_min_f": daily["temperature_2m_min"][idx],
    }


def evaluate_alerts(forecast):
    triggered = []

    if forecast["rain_probability"] >= RAIN_PROBABILITY_THRESHOLD:
        triggered.append(f"Rain likely ({forecast['rain_probability']}% chance)")

    if forecast["snowfall_cm"] > SNOW_THRESHOLD_CM:
        triggered.append(f"Snow expected ({forecast['snowfall_cm']} cm)")

    if forecast["temp_min_f"] < EXTREME_COLD_F:
        triggered.append(f"Extreme cold (low {forecast['temp_min_f']}°F)")

    if forecast["temp_max_f"] > EXTREME_HOT_F:
        triggered.append(f"Extreme heat (high {forecast['temp_max_f']}°F)")

    return triggered


def build_message(forecast, triggered):
    return (
        f"⚠️ Weather Alert for {LOCATION_NAME} — tomorrow ({forecast['date']}):\n"
        f"High {forecast['temp_max_f']}°F, Low {forecast['temp_min_f']}°F, "
        f"Rain chance {forecast['rain_probability']}%, "
        f"Snowfall {forecast['snowfall_cm']} cm.\n"
        f"Triggered: {', '.join(triggered)}."
    )


def send_discord_alert(webhook_url, message):
    response = requests.post(webhook_url, json={"content": message}, timeout=10)
    if not response.ok:
        print(f"Discord responded {response.status_code}: {response.text}", file=sys.stderr)
    response.raise_for_status()


def main():
    load_dotenv()
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    try:
        forecast = fetch_tomorrows_forecast()
    except (requests.RequestException, ValueError, KeyError) as exc:
        print(f"Error fetching forecast: {exc}", file=sys.stderr)
        sys.exit(1)

    triggered = evaluate_alerts(forecast)
    if not triggered:
        print(f"No alert conditions met for {forecast['date']}. Nothing sent.")
        return

    message = build_message(forecast, triggered)
    try:
        send_discord_alert(webhook_url, message)
    except requests.RequestException as exc:
        print(f"Error sending Discord alert: {exc}", file=sys.stderr)
        sys.exit(1)

    print("Alert sent:")
    print(message)


if __name__ == "__main__":
    main()
