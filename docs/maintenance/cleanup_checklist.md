# 💁 pyNance Repository Cleanup & Organization Checklist

## 😂 Directory & File Structure

- [ ] Move `README2md` content (if unique) into `README.md` and delete `README2md`.
- [ ] Rename `DevelopingForecastEnging.txt` \u2023 `DevelopingForecastEngine.txt`.
- [ ] Group mapping files into `docs/maps/`:
  - [] `BackendMap.txt`
  - [] `FrontendMap.txt`
  - [] `LinkAccountFullProducts_Backend_Integration_Map.md`
- [ ] Group dev notes into `docs/devnotes/`:
  - [] `Dev_ForecastReference.md`
  - [] `DevelopingForecast.txt`
  - [] `refresh_route_reviewer.md`
- [ ] Group architecture files into `docs/architecture/`:
  - [] `arch_ux_01.md`
  - [] `arch_ux_02.md`
- [ ] delete `frontend/MIGRIATION_CHECKLIST.md` if empty, or populate with starter content.
- [ ] Create a top-level `tests/` directory or `backend/tests`/ and `frontend/tests/` if not present.

## 🚀 Documentation & Consistency

- [ ] Consolidate multiple `.env` samples under `docs/configuration.md` and reference each `example.env`.
- [ ] Ensure all Markdown files have meaningful titles and clear headers.


## 👀 Tooling Hygiene

- [ ] Delete root-level `package-lock.json` if it's obsolete (backend doesn't appear to use Node.js).
- [ ] Ensure only `frontend/package-lock.json` is tracked by Git.
- [ ] Validate all `package.json`/`requirements.txt` files are up-to-date and not duplicated unnecessarily.

## 📀 Testing & Automation
- [ ] Create `tests/` or `backend/tests/` folder for Python backend tests.
- [ ] Organize Cypress tests properly under `frontend/cypress/`.
- [ ] Add GitHub Actions workflows for:
  - [] Linting (e.g. pre-commit, ESLINT, Black)
  - [] Backend unit tests
  - [] Frontend tests (Jest/Cypress)

## 🔟 Where to Save

Sve this checklist in the following path:
``docs/maintenance/cleanup_checklist.md``
This location is:
- Logical under `docs/`
- Future-friendly discoverable
- Appropriately reflects this report's maintenance score

Would you like this saved and committed?