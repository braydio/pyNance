# pyNance-Dash

pyNance is a personal finance dashboard application that integrates with the Teller API to fetch and manage account and transaction data. It provides a rich frontend built with Vue 3 and Vite and a Flask backend that stores data in an SQL database. The application features account overviews, transaction management (with inline editing), interactive charts (including daily net and category breakdown charts), and draggable interfaces for reordering accounts—all styled with a Gruvbox/Hyprland-inspired theme.

> Note: I'm not 100% sure the onboarding with the Teller.io link process is fully functional. For now I use the test.py file in backend/test.py. If you have issues with account link, get the account token and user id from backend/app/data/TellerTokens.json (or something like that) and put them in the respective fields in test.py (near the bottom by 'if __main__'). Then cd into the same dir as test.py, and with the .venv active run:
```
.venv/Scripts/activate     # If on windows
source .venv/bin/activate  # If better than windows
cd pyNance/backend         # Nav to /backend/
python test.py             # Run logic to save accounts to SQL DB
```
## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Teller Certificates](#teller-certificates)
- [Quickstart](#quickstart)
- [Configuration](#configuration)
- [Development](#development)
  - [Running the Backend](#running-the-backend)
  - [Running the Frontend](#running-the-frontend)
  - [Exposing to Other Devices](#exposing-to-other-devices)
- [Testing](#testing)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Teller API Integration:** Retrieve account and transaction data from the Teller API.
- **Account Management:** Refresh and maintain account data with historical records.
- **Transaction Management:** Inline-edit transactions and save updates to the database.
- **Interactive Charts:** View daily net income/expenses and category breakdowns.
- **Draggable Accounts:** Reorder accounts dynamically.
- **Gruvbox/Hyprland Theme:** A modern, dark-themed UI.

## Architecture

- **Frontend:** Vue 3 with Vite, organized into components, views, composables, services, and assets.
- **Backend:** Flask with SQLAlchemy, integrating Teller API and database operations.

## Installation

### Prerequisites

- Node.js (v14+)
- npm or Yarn
- Python (v3.7+)
- pip

### Backend Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/braydio/pyNance.git
   cd pyNance
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up environment variables:** Create `.env` in the backend folder:
   ```ini
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=your_secret_key
   DATABASE_URL=sqlite:///app.db
   TELLER_APP_ID=your_teller_app_id
   TELLER_ENV=sandbox
   ```
5. **Obtain Teller Certificates:** Place `certificate.pem` and `private_key.pem` in `backend/app/certs`. Follow Teller's documentation to generate them.
6. **Run Database Migrations:**
   ```bash
   python run.py
   ```

### Frontend Setup

1. **Navigate to the frontend folder:**
   ```bash
   cd frontend
   ```
2. **Install dependencies:**
   ```bash
   npm install
   ```
3. **Set up environment variables:** Create `.env` in the frontend folder:
   ```ini
   VUE_APP_API_BASE_URL=http://192.168.1.68:5000/api
   ```

## Quickstart

### Running the Backend
```bash
python run.py
```

### Running the Frontend
```bash
npm run dev
```

### Exposing to Other Devices
- **Backend:** Runs at `http://192.168.1.68:5000`.
- **Frontend:** Ensure `vite.config.js` sets `host: true`.

## Testing
- **Run Cypress tests:**
  ```bash
  npm run test:e2e
  ```
- **Run unit tests:** Use your preferred test runner.

## Deployment
Build the frontend:
```bash
npm run build
```
Deploy using Gunicorn for Flask and serve static files.

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -am 'Add feature'`).
4. Push and open a Pull Request.

## License

MIT License. See [LICENSE](LICENSE) for details.

