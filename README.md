# CLINICAL DATA INTELLIGENCE AGENT

<br>

*This project is a smart AI assistant built for hospitals and clinics. It helps doctors and staff find information quickly by talking to it in plain English. The agent can automatically search through patient records, read medical notes, and even calculate statistics from complex databases. By combining structured data with AI-powered search, it saves hours of manual work and helps healthcare teams make better decisions for their patients.*

![GitHub repo size](https://img.shields.io/github/repo-size/suranjitpartho/clinical-data-intelligence-system?color=blue)
![GitHub last commit](https://img.shields.io/github/last-commit/suranjitpartho/clinical-data-intelligence-system?color=28C78D)
![GitHub top language](https://img.shields.io/github/languages/top/suranjitpartho/clinical-data-intelligence-system?color=red)
![Architecture](https://img.shields.io/badge/architecture-LangGraph-gold)

<br>

> **SITUATION:** Clinical environments suffer from fragmented data. Quantitative metrics (billing/labs) live in rigid SQL databases, while qualitative insights (clinical notes) are locked in unstructured text. Clinicians lose hours waiting for manual data pulls, delaying patient care and operational decisions.

> **TARGET:** The mission was to build a "Clinical Intelligence Layer" that translates natural language into precise database queries.

> **ACTION:** Engineered a deterministic state machine using **LangGraph** to manage complex reasoning loops. Implemented **Proactive Schema Discovery** to fetch real categorical values from the DB and a **Self-Healing SQL** node that autonomously captures PostgreSQL errors and rewrites queries until successful.

> **RESULT:** Reduced data-pull latency from days to **sub-second execution** with near-100% precision. Built a **Reasoning Trace** UI that exposes the agent's internal logic, building critical trust with medical professionals.

<br>

---

### Core Features
*   **LangGraph Orchestration:** State-based reasoning with loops and conditional edges.
*   **Context-Aware Query Transformation:** Rewrites follow-up questions into standalone queries to maintain accuracy in multi-turn conversations.
*   **Proactive Schema Discovery:** The agent fetches real categorical values (e.g., specific status flags) from the DB before writing SQL to eliminate hallucinations.
*   **Hybrid Data Retrieval:** Combines exact-match PostgreSQL with pgvector semantic search.
*   **Glassmorphism UI:** Premium, modern frontend designed with Tailwind CSS.

<br>

### Detailed System Architecture

The system is built on a modular, event-driven architecture designed for clinical precision and high availability.

```mermaid
graph TD
    User([User Query]) --> Rewrite[Query Rewrite Node]
    Rewrite --> Router{Intent Router}
    
    Router -->|Structured| Discovery[Schema Discovery]
    Discovery --> SQL[SQL Execution Node]
    Router -->|Unstructured| RAG[Semantic RAG Node]
    Router -->|General| Synth[Synthesis Node]
    
    SQL -->|Syntax Error| SQL_Retry[Self-Correction Loop]
    SQL_Retry --> SQL
    SQL -->|Data Found| Synth
    
    RAG -->|Medical Context| Synth
    Synth --> Output([Clinical Insight])
    
    subgraph "Hybrid Data Layer"
    Postgres[(PostgreSQL)]
    Vector[(pgvector Index)]
    end
    
    SQL -.-> Postgres
    RAG -.-> Vector
```

**1. The Reasoning Engine (LangGraph)**  
Unlike traditional linear chains, this agent uses a **State Graph** to allow for cycles and conditional logic. This enables the agent to "pause" and verify data before responding, ensuring that clinical assumptions are backed by database evidence.

**2. Self-Healing SQL & Proactive Discovery**  
The agent implements a two-stage strategy for structured data:
*   **Discovery:** It first queries the database metadata to find valid categorical values (e.g., interpreting "active" vs "ACTIVE").
*   **Self-Correction:** If the generated SQL fails, the PostgreSQL error is fed back into the agent's context for an autonomous rewrite.

**3. Hybrid Clinical Context (RAG + SQL)**  
The system treats the database and clinical notes as two distinct but complementary sources of truth:
*   **Structured Analysis:** Performs complex aggregations (averages, trends, counts) via exact SQL.
*   **Semantic Intelligence (RAG):** Retrieves narrative context (patient history, symptom patterns) using **pgvector** and the **BAAI/bge-m3** embedding model, ensuring the final answer is clinically nuanced.

<br>

[![Tech Stack Icons](https://skillicons.dev/icons?i=py,fastapi,postgres,react,tailwind,vite&theme=dark)](https://skillicons.dev)
![LangChain](https://img.shields.io/badge/LangChain-1C1C1C?style=for-the-badge&logo=langchain&logoColor=white) ![LangGraph](https://img.shields.io/badge/LangGraph-1C1C1C?style=for-the-badge&logo=langchain&logoColor=white)

<br>

---

### Developer Guide

**1. Backend Setup**
```bash
git clone https://github.com/suranjitpartho/clinical-data-intelligence-system.git
cd clinical-data-intelligence-system
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python scripts/seed_data.py
python scripts/generate_embeddings.py  # Generate AI vectors for RAG
uvicorn app.main:app --reload --port 8000
```

**2. Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

**3. Testing & Validation**
```bash
# Run agent logic tests
python scripts/test_agent.py

# Run semantic search validation
python scripts/test_search.py
```

<br>

*Engineered with precision for the modern clinical data landscape.*
