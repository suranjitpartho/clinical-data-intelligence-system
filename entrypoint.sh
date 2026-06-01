#!/bin/sh

APP_PORT="${PORT:-8000}"

# ─── Validate required env vars ────────────────────────────────────
if [ -z "$GROQ_API_KEY" ]; then
    echo "ERROR: GROQ_API_KEY is not set."
    echo "  Create .env from .env.example with your keys: cp .env.example .env"
    exit 1
fi
if [ -z "$GITHUB_CLIENT_ID" ]; then
    echo "ERROR: GITHUB_CLIENT_ID is not set."
    echo "  Create .env from .env.example with your keys: cp .env.example .env"
    exit 1
fi
if [ -z "$GITHUB_CLIENT_SECRET" ]; then
    echo "ERROR: GITHUB_CLIENT_SECRET is not set."
    echo "  Create .env from .env.example with your keys: cp .env.example .env"
    exit 1
fi

echo "--- 🚀 Starting Clinical AI System Initialization ---"

# 0. Wait for database to be reachable
echo "--- 🗄️  Checking Database Connection ---"
python -c "
import os, time, psycopg2

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

# 4. Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT}"
