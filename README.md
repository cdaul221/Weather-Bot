# Weather Alert Bot

Checks tomorrow's forecast for Chicago, IL (Open-Meteo API, no API key needed)
and posts a Discord alert only when rain, snow, or extreme temperatures are
expected. Sends nothing on unremarkable days.

## Alert conditions

- Rain: ≥50% max daily precipitation probability
- Snow: any measurable snowfall
- Extreme cold: forecast low below 20°F
- Extreme heat: forecast high above 95°F

Edit the constants at the top of `weather_alert_bot.py` to change the
location or thresholds.

## Setup

1. Create a Discord webhook: in your server, go to
   **Channel Settings → Integrations → Webhooks → New Webhook**, then copy
   the webhook URL.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
