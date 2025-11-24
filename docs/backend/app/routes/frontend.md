# Frontend Route (`frontend.py`)

## Purpose

Serve metadata and configuration that bootstrap the UI, including layout descriptors and user-specific settings.

## Endpoints

- `GET /frontend/layout` – Return the UI layout schema and feature flags.
- `GET /frontend/settings` – Retrieve stored UI preferences and onboarding flags.
- `POST /frontend/settings` – Persist updated UI preferences.

## Inputs/Outputs

- **GET /frontend/layout**
  - **Inputs:** None.
  - **Outputs:** Layout definition with panel ordering and feature flags.
- **GET /frontend/settings**
  - **Inputs:** None.
  - **Outputs:** JSON object containing settings such as theme, onboarding completion, and preferred view.
- **POST /frontend/settings**
  - **Inputs:** JSON payload with settings keys to update.
  - **Outputs:** Updated settings echoed back with success status.

## Auth

- Uses standard user authentication; preferences are stored per user/device context.

## Dependencies

- `models.UserPreferences` and related settings storage utilities.
- Service helpers that manage defaults based on browser environment or stored state.

## Behaviors/Edge Cases

- Defaults are inferred on first use and overridden on subsequent updates.
- Settings persistence may be device-specific depending on storage strategy.

## Sample Request/Response

```http
POST /frontend/settings HTTP/1.1
Content-Type: application/json

{ "theme": "dark", "preferred_view": "table" }
```

```json
{ "theme": "dark", "onboarding_complete": true, "preferred_view": "table" }
```
