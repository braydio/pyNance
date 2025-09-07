# Arbit Dashboard

The Arbit dashboard surfaces key arbitrage metrics from backend services to the frontend.

## Configuration
- Set `ARBIT_API_BASE` in `backend/.env` to point at the Arbit service.
- Ensure `frontend/.env` contains matching `VITE_ARBIT_API_BASE` for proxying.

## Endpoints
- `GET /api/arbit/positions`: current open positions.
- `GET /api/arbit/stats`: aggregated statistics.
- `POST /api/arbit/refresh`: trigger manual refresh.

## UI
Visit `/arbit` in the frontend to access the dashboard. The view polls the above endpoints and displays charts for active positions and performance over time.

> TODO: add screenshots or GIFs once the UI stabilizes.

