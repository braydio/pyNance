# pyNance development environment variables
# Copy this template to your home directory to persist settings.

# --- Python & Flask ---
export FLASK_ENV="production"
export LOG_LEVEL="INFO"
export SQL_ECHO="false"
export DATABASE_NAME="developing_dash.db"
export CLIENT_NAME="pyNance-Dash"

# --- Plaid configuration ---
export PLAID_CLIENT_ID=""
export PLAID_SECRET_KEY=""
export PLAID_SECRET=""
export PLAID_ENV="sandbox"
export PRODUCTS="transactions"

# --- Teller configuration ---
export TELLER_APP_ID=""
export TELLER_WEBHOOK_SECRET=""

# --- Miscellaneous tokens ---
export VARIABLE_ENV_TOKEN=""
export VARIABLE_ENV_ID=""

# --- Frontend (Vite) configuration ---
export VITE_SESSION_MODE="development"
export VITE_APP_API_BASE_URL="http://localhost:5000/api"
export VITE_TELLER_APP_ID=""
export VITE_TELLER_ENV="sandbox"
export VITE_PLAID_CLIENT_ID=""
export VITE_USER_ID_PLAID=""
export PHONE_NBR="+10000000000"

# --- Vector DB / LLM tooling ---
export CHROMA_COLLECTION="pynance-code"
export CHROMA_RESULT_COUNT="3"
export CHROMA_HOST="localhost"
export CHROMA_PORT="8055"
export CHROMA_MODEL="all-MiniLM-L6-v2"

export QDRANT_HOST="localhost"
export QDRANT_PORT="6333"
export QDRANT_COLLECTION="pynance-code"
export QDRANT_URL="http://localhost:6333"

export LOCALAI_URL="http://localhost:5051"
export LOCALAI_MODEL="my_model"
export TEXTGEN_URL="http://localhost:5051"

export RETRIEVAL_LIMIT="5"
export MAX_ITERATIONS="10"
export RETRY_DELAY="1.0"

# --- Virtual environment activation ---
PROJECT_ROOT="$(dirname "${BASH_SOURCE[0]}")"
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi
