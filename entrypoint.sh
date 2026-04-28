#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "--- 🚀 Starting Clinical AI System Initialization ---"

# 1. Run database migrations
echo "--- 🧬 Running Database Migrations ---"
alembic upgrade head

# 2. Seed clinical data
echo "--- 📝 Seeding Clinical Data ---"
python scripts/seed_data.py

# 3. Generate medical embeddings
echo "--- 🧠 Generating Semantic Embeddings (BGE-M3) ---"
python scripts/generate_embeddings.py

echo "--- ✅ System Initialized. Starting FastAPI Server ---"

# 4. Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
