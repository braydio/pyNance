# Serenity Evening Guide

This guide blends pyNance features with a tranquil yet engaging evening routine.
It highlights how the project's tooling can complement relaxation and mindful
financial check‑ins.

## 1. Early Evening Setup

1. **Review the Dashboard**  
   Launch the Flask backend with `flask run --app backend.run` and open the Vue
   frontend (`npm run dev`). The dashboard provides access to:
   - `/accounts/get_accounts` for a quick account overview.
   - `/transactions/get_transactions` to scan recent spending.
2. **Forecast Snapshot**  
   Use the forecasting module outlined in `docs/FORECAST_PURPOSE.md` to preview
   upcoming expenses. The `forecast_engine.py` and related helpers transform your
   transaction history into a clear projection.

## 2. Dinner Break at 9 PM

Order takeout from your favorite spot just before 9&nbsp;PM. While you wait for
pickup or delivery, note the transaction via the `/api/transactions` endpoint or
add a manual adjustment in the `ForecastAdjustmentsForm.vue` component.

## 3. Relaxation with Insight

- **Check Account History**  
  Browse the aggregated history described in
  `docs/dataflow/account_history_aggregation.md` to see how today's spending fits
  into your overall trends.
- **Logs for Peace of Mind**  
  If something feels off, inspect `backend/app/logs/app.log` as mentioned in the
  README for detailed traces.

## 4. Engaging Yet Calm

Spend time exploring `ForecastChart.vue` in the frontend. The visualization of
projected vs. actual balances offers gentle stimulation while staying aligned
with personal finance goals.

When the takeout arrives, enjoy your meal and unplug from the screens. The
dashboard will be ready whenever you return, keeping your finances organized
without intruding on downtime.

## 5. Wind Down

Close the evening by glancing at the balance charts and verifying that your
transaction was logged correctly. Then shut down the dev servers:

```bash
Ctrl+C  # stop Flask and Vite
```

Feel free to journal or meditate after reviewing your accounts. pyNance supports
both engagement and tranquility—helping you stay informed without disrupting the
peace of your evening.
