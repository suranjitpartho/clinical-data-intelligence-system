#!/bin/sh

# ─── Interactive Setup: API Keys ───────────────────────────────────
# Load previously saved env vars from the persistent volume
ENV_DIR="/app/env"
ENV_FILE="$ENV_DIR/.env"
mkdir -p "$ENV_DIR"
if [ -f "$ENV_FILE" ]; then
    . "$ENV_FILE"
fi
touch "$ENV_FILE"

save_env() {
    var_name="$1"
    var_value="$2"
    if [ -f "$ENV_FILE" ]; then
        grep -v "^${var_name}=" "$ENV_FILE" > "$ENV_FILE.tmp" 2>/dev/null || true
        cp "$ENV_FILE.tmp" "$ENV_FILE"
        rm -f "$ENV_FILE.tmp"
    fi
    echo "${var_name}=${var_value}" >> "$ENV_FILE"
}

# Non-interactive mode: fail if required vars are missing
if [ ! -t 0 ] && { [ -z "$GROQ_API_KEY" ] || [ -z "$GITHUB_CLIENT_ID" ] || [ -z "$GITHUB_CLIENT_SECRET" ]; }; then
    echo "ERROR: Running in non-interactive mode but required env vars are missing."
    echo ""
    echo "  First time? Run interactively:     docker compose up"
    echo "  Already configured? Run detached:  docker compose up -d"
    exit 1
fi

if [ -t 0 ]; then
    exec < /dev/tty
    echo ""
    echo "==========================================="
    echo "  Clinical Data Intelligence — Setup"
    echo "==========================================="
    echo ""

    # ── GROQ_API_KEY ──
    if [ -z "$GROQ_API_KEY" ]; then
        echo "========================================"
        echo "STEP 1: GROQ_API_KEY (required)"
        echo "========================================"
        echo "We need an API key from Groq to run the AI models."
        echo "Getting one is free and takes 2 minutes:"
        echo ""
        echo "  1. Go to https://console.groq.com"
        echo "  2. Sign up for a free account"
        echo "  3. Go to API Keys section"
        echo "  4. Click 'Create API Key'"
        echo "  5. Copy the key (it starts with 'gsk_')"
        echo ""
        printf "Paste your GROQ_API_KEY: "
        read -r input_value
        while [ -z "$input_value" ]; do
            echo "GROQ_API_KEY is required. Paste the key or press Ctrl+C to exit."
            printf "Paste your GROQ_API_KEY: "
            read -r input_value
        done
        export GROQ_API_KEY="$input_value"
        save_env "GROQ_API_KEY" "$input_value"
        echo ""
    fi

    # ── GITHUB_CLIENT_ID ──
    if [ -z "$GITHUB_CLIENT_ID" ]; then
        echo "========================================"
        echo "STEP 2: GitHub OAuth (required for login)"
        echo "========================================"
        echo "You need a GitHub OAuth app so you can log in."
        echo "Create one (it takes 3 minutes):"
        echo ""
        echo "  1. Go to https://github.com/settings/developers"
        echo "  2. Click 'New OAuth App'"
        echo "  3. Application name: Clinical AI (or anything)"
        echo "  4. Homepage URL: http://localhost:8000"
        echo "  5. Callback URL: http://localhost:8000/api/auth/github/callback"
        echo "  6. Click 'Register application'"
        echo "  7. Copy the Client ID from the next page"
        echo ""
        printf "Paste your GITHUB_CLIENT_ID: "
        read -r input_value
        while [ -z "$input_value" ]; do
            echo "GITHUB_CLIENT_ID is required."
            printf "Paste your GITHUB_CLIENT_ID: "
            read -r input_value
        done
        export GITHUB_CLIENT_ID="$input_value"
        save_env "GITHUB_CLIENT_ID" "$input_value"
        echo ""
    fi

    # ── GITHUB_CLIENT_SECRET ──
    if [ -z "$GITHUB_CLIENT_SECRET" ]; then
        echo "  Now generate a Client Secret for the same app:"
        echo "    1. On the same page, click 'Generate a new client secret'"
        echo "    2. Copy the secret key shown"
        echo ""
        printf "Paste your GITHUB_CLIENT_SECRET: "
        read -r input_value
        while [ -z "$input_value" ]; do
            echo "GITHUB_CLIENT_SECRET is required."
            printf "Paste your GITHUB_CLIENT_SECRET: "
            read -r input_value
        done
        export GITHUB_CLIENT_SECRET="$input_value"
        save_env "GITHUB_CLIENT_SECRET" "$input_value"
        echo ""
    fi

    # ── LANGFUSE (optional) ──
    if [ -z "$LANGFUSE_SECRET_KEY" ]; then
        echo "========================================"
        echo "STEP 3: Langfuse (optional)"
        echo "========================================"
        echo "Langfuse tracks AI queries for the Analytics dashboard."
        echo "You can skip this if you don't need analytics."
        echo ""
        echo "  To get keys (if you want):"
        echo "    1. Go to https://cloud.langfuse.com"
        echo "    2. Sign up (free tier)"
        echo "    3. Create a project"
        echo "    4. Go to Project Settings -> API Keys"
        echo ""
        printf "Paste LANGFUSE_SECRET_KEY (or press Enter to skip): "
        read -r input_value
        if [ -n "$input_value" ]; then
            export LANGFUSE_SECRET_KEY="$input_value"
            save_env "LANGFUSE_SECRET_KEY" "$input_value"

            printf "Paste LANGFUSE_PUBLIC_KEY: "
            read -r input_value2
            if [ -n "$input_value2" ]; then
                export LANGFUSE_PUBLIC_KEY="$input_value2"
                save_env "LANGFUSE_PUBLIC_KEY" "$input_value2"
            fi
        fi
        echo ""
    fi

    # ── JWT_SECRET (auto-generate) ──
    if [ -z "$JWT_SECRET" ]; then
        JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
        export JWT_SECRET
        save_env "JWT_SECRET" "$JWT_SECRET"
        echo "  JWT_SECRET auto-generated."
        echo ""
    fi

    # ── Default env settings ──
    ENV="${ENV:-local}"
    DEBUG="${DEBUG:-true}"
    FRONTEND_URL="${FRONTEND_URL:-http://localhost:8000}"
    AI_PROVIDER="${AI_PROVIDER:-groq}"
    AI_MODEL="${AI_MODEL:-llama-3.3-70b-versatile}"
    LANGFUSE_HOST="${LANGFUSE_HOST:-https://cloud.langfuse.com}"
    save_env "ENV" "$ENV"
    save_env "DEBUG" "$DEBUG"
    save_env "FRONTEND_URL" "$FRONTEND_URL"
    save_env "AI_PROVIDER" "$AI_PROVIDER"
    save_env "AI_MODEL" "$AI_MODEL"
    save_env "LANGFUSE_HOST" "$LANGFUSE_HOST"

    echo "==========================================="
    echo "  Setup complete! Starting server..."
    echo "==========================================="
    echo ""
fi

APP_PORT="${PORT:-8000}"

echo "--- 🚀 Starting Clinical AI System Initialization ---"

# 0. Wait for database to be reachable
echo "--- 🗄️  Checking Database Connection ---"
python -c "
import os, time, psycopg2
from urllib.parse import quote_plus

for attempt in range(30):
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            port=int(os.environ.get('DB_PORT', 5432)),
            dbname=os.environ.get('DB_NAME', 'clinical_db'),
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASS', ''),
            connect_timeout=5,
        )
        conn.close()
        print('Database connection successful')
        break
    except Exception as e:
        if attempt < 29:
            print(f'Waiting for database... ({attempt + 1}/30)')
            time.sleep(2)
        else:
            print(f'Failed to connect to database: {e}')
            exit(1)
"

# 1. Run database migrations
echo "--- 🧬 Running Database Migrations ---"
alembic upgrade head

# 2. Seed clinical data (skips if already seeded)
echo "--- 📝 Seeding Clinical Data ---"
PYTHONPATH=. python scripts/seed_data.py

# 3. Generate embeddings in background — server starts immediately
echo "--- 🧠 Generating Semantic Embeddings (BGE-M3) in background ---"
PYTHONPATH=. nohup python scripts/generate_embeddings.py > /tmp/embeddings.log 2>&1 &
EMBEDDING_PID=$!
echo "--- Embedding process running in background (PID: ${EMBEDDING_PID}) ---"

echo "--- ✅ System Initialized. Starting FastAPI Server on port ${APP_PORT} ---"

# 5. Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT}"
