# CLAUDE.md for Claude Code Context

---

## **pyNance Directory Map**

---

### **Backend (`backend/`)**

```
backend/
├── .flaskenv
├── Procfile
├── cron_sync.py
├── docker-compose.yml
├── example.env
├── load_transactions.py
├── recurring_flags.txt
├── run.py
├── app/
│   ├── __init__.py        # Main Flask app/init, all blueprints, setup, CORS, error handlers, DB, etc
│   ├── extensions.py      # SQLAlchemy import
│   ├── models.py          # All SQLAlchemy models (accounts, users, transactions, etc)
│   ├── certs/
│   ├── cli/
│   ├── config/
│   ├── helpers/
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── accounts.py
│   │   ├── auth.py
│   │   ├── categories.py
│   │   ├── charts.py
│   │   ├── health.py
│   │   ├── recurring.py
│   │   ├── teller.py
│   │   └── transactions.py
│   ├── services/
│   │   └── (service-layer files: api abstraction, business logic)
│   ├── sql/
│   │   └── (programmatic queries/business logic)
│   ├── static/
│   │   └── (static files for Flask serving)
│   └── utils/
│       └── (utility functions for backend)
├── dev/
├── migrations/
├── scripts/
└── temp_migrations/
```

---

### **Frontend (`frontend/`)**

```
frontend/
├── .editorconfig
├── .gitattributes
├── .gitignore
├── .husky/
├── .prettierrc.json
├── Dev_Checklist.md      # Large dev onboarding/progress doc
├── README.md
├── backups/
├── cypress.config.js
├── cypress/
├── eslint.config.js
├── example.env
├── frontend_lint.txt
├── index.html
├── jsconfig.json
├── package-lock.json
├── package.json
├── public/
├── scripts/
├── src/
│   ├── App.vue
│   ├── OldAccountReorder.vue
│   ├── auto-imports.d.ts
│   ├── components.d.ts
│   ├── api/
│   │   ├── MIGRATIONS_CHECKLIST.md
│   │   ├── accounts.js
│   │   ├── accounts_link.js
│   │   ├── arbitrage.js
│   │   ├── categories.js
│   │   ├── charts.js
│   │   ├── recurring.js
│   │   ├── teller.js
│   │   └── transactions.js
│   ├── assets/
│   ├── components/
│   │   ├── __tests__/
│   │   ├── backups/
│   │   ├── base/
│   │   ├── charts/
│   │   ├── forecast/
│   │   ├── forms/
│   │   ├── layout/
│   │   ├── modals/
│   │   ├── recurring/
│   │   ├── tables/
│   │   ├── ui/
│   │   ├── unused/
│   │   └── widgets/
│   ├── composables/
│   ├── main.js
│   ├── mocks/
│   ├── router/
│   ├── services/
│   ├── styles/
│   ├── utils/
│   └── views/
├── stats.html
├── tailwind.config.js
├── vite.config.js
└── workflow
```

---

## **Context & Key Points for a `CLAUDE.md` File**

### **High-level project purpose**

- Full-stack personal finance app.
- Frontend: Vue 3 + Vite + Tailwind, modular component structure, composables for state logic, API-layer abstraction.
- Backend: Flask app using blueprints for modular REST routes, SQLAlchemy ORM, Marshmallow serialization, service-layer for business logic, Postgres (via SQLAlchemy).

### **Design & Data Flow**

- API endpoints handled by Flask blueprints, matching FE `/api/*.js` calls.
- Typical pattern: `/api/route.js` → `app/routes/route.py` → `services/` → `models.py`
- State management is handled per-page/composable on FE, not via Vuex or Pinia (as far as visible).
- Charts/tables are driven by backend API data, not by static/mocked data.
- Modal, chart click, and drill-down: event → state set → modal opens with filtered array (client-side).

### **Dev Process & Structure**

- Organized by feature/concern on both FE/BE (`charts`, `accounts`, `categories`, `transactions`, etc.).
- Active use of TypeScript d.ts for FE type hints, Prettier/ESLint enforced, Cypress for E2E testing.
- Dev checklist and migrations checklist for onboarding.

### **Planned/Noted Features**

- Frontend code, comments, and dev checklist suggest: More insights, analytics, advanced drill-downs, recurring tx logic, possibly future ML-driven prediction.
- Backend has full recurring tx logic, custom queries for analytics, and modular structure for rapid expansion.

---

## **Summary**

This is a modular, maintainable full-stack Vue/Flask finance app with strong separation of concerns. API-first design. All state/data is live-loaded from the backend. Modal and drill-down logic always filters from the most up-to-date loaded array in the FE, not from re-calling the backend (unless explicitly needed).

**If you need a sample or further code context for any file/feature, let me know!**
