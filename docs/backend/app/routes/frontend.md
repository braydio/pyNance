# backend/app/routes Documentation

---

## 📘 `frontend.py`

````markdown
# Frontend Route

## Purpose

Serves metadata and configuration necessary for frontend rendering and bootstrapping. This includes layout descriptors, onboarding flags, and settings that influence the UI state.

## Key Endpoints

- `GET /frontend/layout`: Returns UI layout schema.
- `GET /frontend/settings`: Retrieves UI preferences and flags.
- `POST /frontend/settings`: Updates UI flags and state.

## Inputs & Outputs

- **GET /frontend/layout**

  - **Output:**
    ```json
    {
      "panels": ["chart", "transactions", "summary"],
      "feature_flags": { "forecast": true, "recurring": false }
    }
    ```

- **GET /frontend/settings**

  - **Output:**
    ```json
    {
      "theme": "dark",
      "onboarding_complete": true,
      "preferred_view": "table"
    }
    ```

- **POST /frontend/settings**
  - **Input:** JSON object with any settings keys
  - **Output:** Status code with updated payload echo

## Internal Dependencies

- `models.UserPreferences`
- `services.settings_store`

## Known Behaviors

- Settings persisted per device.
- Defaults inferred from browser environment on first use.
- Overrides persisted for returning sessions.

## Related Docs

- [`docs/frontend/components/LayoutManager.md`](../../frontend/components/LayoutManager.md)
- [`docs/dataflow/ui_config_pipeline.md`](../../dataflow/ui_config_pipeline.md)
````

---
