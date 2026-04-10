# Clinical Data Intelligence System (AI + RAG)

An AI-powered clinical data intelligence system designed for a fictional private medical clinic in New Zealand.

This system demonstrates the integration of **LangGraph AI Agents** with both structured relational data (SQL) and unstructured clinical notes (Vector RAG) to provide real-time clinical insights.

## 🚀 Key Features

- **Hybrid AI Agent:** Automatically routes queries between a PostgreSQL database (SQL Tool) and Clinical Notes (RAG Tool).
- **Self-Correction Loop:** The agent identifies SQL syntax errors or retrieval failures and automatically regenerates queries using Claude AI.
- **RAG via pgvector:** high-performance vector similarity search over appointment clinical notes.
- **Auditability & Compliance:** Every AI decision and tool query is logged in an `audit_logs` table for compliance with NZ health information standards.
- **High-Volume Seeding:** Built-in scripts to generate synthetic clinical data (5,000+ records) using realistic medical language.

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python)
- **AI Agent:** LangGraph & LangChain
- **LLM/Embeddings:** Claude API (Anthropic)
- **Database:** PostgreSQL + `pgvector`
- **ORM:** SQLAlchemy + Alembic
- **Frontend:** React + Vite + Tailwind CSS

## 📂 Project Structure

```text
/app
  /api        # FastAPI endpoints
  /models     # SQLAlchemy database models
  /services   # AI Agent logic and RAG implementation
  /db         # Database configuration
/scripts      # Data seeding scripts
/migrations   # Alembic schema versions
```

## ⚙️ Quick Start

1. **Environment Setup:**
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   # Fill in your ANTHROPIC_API_KEY and DATABASE_URL
   ```

2. **Database Migrations:**
   ```bash
   alembic upgrade head
   ```

3. **Run the API:**
   ```bash
   uvicorn app.main:app --reload
   ```

---
*Created for AI Engineer Portfolio — New Zealand Domain Context.*
