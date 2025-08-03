# R/S Arbitrage Monitor

A lightweight view that displays real time updates from the Discord bot.

The bot writes JSON to `backend/app/logs/rs_arbitrage.json`. The new
`/api/arbitrage/current` endpoint exposes the latest snapshot so the
Vue page can poll for updates.

Visit `/arbitrage` in the frontend to see the data refresh every few
seconds.
