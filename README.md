# CLINICAL DATA INTELLIGENCE SYSTEM

*The Clinical Data Intelligence System is an AI platform designed to make clinical information easy to access through simple, natural conversation. It enables doctors and healthcare staff to instantly search patient records, medical notes, and lab results without needing technical database skills. By seamlessly integrating structured database records with unstructured clinical notes, the system automates manual reporting and provides clear insights that help medical teams save time and provide better care for their patients.*

![Release](https://img.shields.io/badge/Release-v1.0-48C784)
![Platform](https://img.shields.io/badge/Platform-Web-CDDE21)
![Size](https://img.shields.io/github/repo-size/suranjitpartho/clinical-data-intelligence-system?label=Size&color=E34F79)
![Last Commit](https://img.shields.io/github/last-commit/suranjitpartho/clinical-data-intelligence-system?label=Last%20Commit&color=F0B960)
![Top Language](https://img.shields.io/github/languages/top/suranjitpartho/clinical-data-intelligence-system?color=red)
![Stars](https://img.shields.io/github/stars/suranjitpartho/clinical-data-intelligence-system?label=Stars&style=flat&color=gold)
![License](https://img.shields.io/github/license/suranjitpartho/clinical-data-intelligence-system?label=License&color=informational)

<br>

<div align="center">
  <img src="./frontend/src/assets/screenshot.png" alt="System Demo" width="100%">
</div>

<br>

## Case Study: Solving Clinical Data Fragmentation

> ⭐ **SITUATION:** Clinical environments suffer from fragmented data. Quantitative metrics (billing/labs) live in rigid SQL databases, while qualitative insights (clinical notes) are locked in unstructured text. Clinicians lose hours waiting for manual data pulls, delaying patient care and operational decisions.
>
> ⭐ **TARGET:** The mission was to build a "Clinical Intelligence Layer" that translates natural language into precise database queries.
>
> ⭐ **ACTION:** Engineered a deterministic state machine using *LangGraph* to orchestrate a hybrid retrieval system. Implemented a *Semantically Augmented Data Dictionary* to bridge clinical logic with SQL schemas, integrated *pgvector* for narrative medical searches, and built a *Proactive Discovery & Self-Healing loop* that autonomously corrects database hallucinations in real-time.
>
> ⭐ **RESULT:** Reduced clinical data retrieval workflows from hours or manual ticket-based requests to near real-time responses, significantly improving operational turnaround. Built a *Reasoning Trace* UI that exposes the agent's internal logic, designed to improve user trust and transparency for clinical workflows. 

<br>

## Core Capabilities

| Feature | Clinical Benefit |
| :--- | :--- |
| **Self-Healing SQL** | Eliminates manual query fixes by autonomously correcting syntax errors. |
| **Proactive Discovery** | Prevents hallucinations by fetching real categorical values before writing SQL. |
| **Hybrid Retrieval** | Combines exact lab results with semantic insights from clinical notes. |
| **Contextual Rewrite** | Maintains diagnostic accuracy in multi-turn conversations by resolving pronouns. |

<br>

## Technical Architecture

The system is built on a modular, state-managed architecture designed for high availability and clinical precision.

![Python](https://img.shields.io/badge/Python-3.11+-1C96E8?logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-22C982?logo=fastapi&logoColor=white) ![LangGraph](https://img.shields.io/badge/LangGraph-0.0.30-DBD51D?logo=langchain&logoColor=white) ![React](https://img.shields.io/badge/React-19.2-2572CF?logo=react&logoColor=white) ![Tailwind](https://img.shields.io/badge/Tailwind-4.2-1FD1CB?logo=tailwindcss&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-7078C4?logo=postgresql&logoColor=white)


<div align="center">
  <img src="./frontend/src/assets/architecture_diagram2.png" alt="System Architecture" width="100%">
</div>

<br>

#### End-to-End Request Flow

1.  **Natural Language Input**: User enters a query (e.g., *"Show abnormal lab results for Patient A"*).
2.  **Contextual Rewrite**: The system resolves conversation history and converts ambiguous prompts into standalone, context-rich queries.
3.  **Intent Routing**: The Orchestrator determines if the request requires *SQL retrieval* (structured labs), *Semantic RAG* (clinical notes), or a *Hybrid response*.
4.  **Multi-Modal Retrieval**: 
    - **SQL Node**: Queries structured tables using schema-aware logic.
    - **RAG Node**: Searches clinical notes and protocols using *pgvector*.
5.  **Validation & Self-Correction**: Any SQL syntax errors or schema mismatches capture the *PostgreSQL traceback*, triggering an autonomous retry loop for immediate self-correction.
6.  **Synthesis Layer**: Combines structured data and unstructured evidence into a single, grounded clinical response.
7.  **Reasoning Trace**: The execution path is exposed to the UI, providing full transparency of the AI’s decision-making process.

<br>

#### System Stack Overview

| Layer | Component / Tech | Key Responsibility |
| :--- | :--- | :--- |
| **Orchestration** | **LangGraph** | Managing state-based clinical reasoning and tool loops. |
| **Knowledge Layer** | **Data Dictionary** | Mapping natural language to complex clinical business logic. |
| **Observability** | **Langfuse** | Capturing LLM latency, token usage, and graph execution traces. |
| **API Backend** | **FastAPI** | Providing high-concurrency, sub-second response times. |
| **Knowledge Base** | **pgvector** | Storing medical narratives and protocol embeddings. |
| **Modern UI** | **React 19** | Delivering a transparent "Reasoning Trace" for clinician trust. |

<br>

## Engineering Deep Dive: Challenges & Solutions

✴️ **Challenge: Managing Non-Linear Clinical Logic → Solution: State-Machine Orchestration**  
At its core, the system utilizes a *LangGraph-driven State Graph* to manage complex reasoning. Unlike basic linear chains, this architecture allows for *directed cycles*, enabling the agent to revisit previous steps if conditions aren't met. This state-managed approach allows the system to generate a *Reasoning Trace*, exposing its internal "Chain of Thought" to clinicians for verification before final synthesis.

✴️ **Challenge: Conversational Context Drift → Solution: Recursive Query Transformation**  
To support natural, multi-turn dialogue, the system implements an intelligent *Query Rewrite Node*. This node uses LLM-based transformation to turn ambiguous follow-up questions (e.g., *"What about his labs?"*) into standalone, context-rich queries (*"Show laboratory results for Patient X"*). This prevents "memory contamination" and ensures the intent router always receives a clear, precise instruction.

✴️ **Challenge: Fragmented Patient Histories → Solution: Multi-Modal Data Fusion (SQL + RAG)**  
To provide a 360-degree patient view, the system implements a *multi-modal retrieval strategy*. It simultaneously pulls quantitative data (billing, labs) via exact-match SQL and qualitative narratives (symptoms, history) via semantic search. By utilizing the *BGE-M3* embedding model and *pgvector*, the system captures subtle medical nuances that traditional keyword search would miss.

✴️ **Challenge: SQL Hallucination & Syntactic Errors → Solution: Proactive Discovery & Self-Correction**  
To guarantee precision, the system employs *Proactive Schema Discovery* guided by a *schema-aware data dictionary*. Before generating SQL, the agent consults a custom knowledge map that defines complex clinical relationships and business rules (e.g., precise age-calculation logic). It then fetches real-time categorical values from the database to ensure the query is perfectly grounded in live data. If a query fails, an autonomous *Self-Correction Loop* captures the database error and feeds it back to the agent for an immediate, self-healing rewrite.

<br>

## Technical Rationale: Why This Stack?

*   **LangGraph over LangChain**: Unlike standard chains, LangGraph provides the fine-grained control over *cycles and state* required for a non-linear clinical diagnostic flow.
*   **PostgreSQL + pgvector over Pinecone**: By using pgvector, the system can perform complex SQL joins and semantic vector searches within a *single transaction*, ensuring data consistency between structured records and clinical notes.
*   **FastAPI over Django**: Chosen for its high-performance asynchronous capabilities, enabling the sub-second response times critical for real-time medical consultation environments.
*   **Advanced Prompt Strategy**: Utilizes *Dynamic Context Injection* and *Few-Shot Clinical Examples*. The system programmatically assembles prompts by combining the User Query, the Data Dictionary, and real-time database categories, ensuring the LLM operates with "Ground Truth" rather than relying on internal weights.

<br>

## Trust & Transparency

*   **Reasoning Trace**: The system exposes its internal "Chain of Thought" to the user, allowing clinicians to verify the logic behind every data retrieval and synthesis.
*   **Observability & Tracing**: Integrated with **Langfuse** for real-time monitoring of LLM metrics (latency, token, costs) and full visualization of the LangGraph execution tree to ensure production-grade reliability.
*   **Audit Accountability**: Every interaction is logged with precise tool usage and raw query data (via `AuditLog`), ensuring a transparent audit trail for all clinical intelligence activities.
*   **Deterministic Guardrails**: Using LangGraph, the system enforces a strict state-managed flow, preventing the AI from wandering into "creative" or ungrounded responses.
*   **Clinical Simulation & Privacy**: To ensure absolute privacy and HIPAA compliance, this system operates on a **proprietary synthetic dataset**. I engineered a custom **Clinical Simulation Engine** that generates high-entropy patient records and longitudinal narratives for rigorous testing.

<br>

## Project Structure

```text
├── app/               # FastAPI Backend (Graph logic, Nodes, Models)
├── frontend/          # React 19 + Tailwind 4 Frontend
├── migrations/        # SQLAlchemy/Alembic Database Migrations
├── scripts/           # Data Seeding & BGE-M3 Embedding Generation
├── app/services/      # Core Data Dictionary & AI Prompts
└── requirements.txt   # Backend dependencies
```

<br>

## Installation & Setup

### 1. Backend Configuration
```bash
# Clone the repository
git clone https://github.com/suranjitpartho/clinical-data-intelligence-system.git
cd clinical-data-intelligence-system

# Environment Setup
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt

# Database & AI Initialization
cp .env.example .env
alembic upgrade head
python scripts/seed_data.py
python scripts/generate_embeddings.py  # Critical: Generates vector vectors for RAG

# Launch API
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Configuration
```bash
cd frontend
npm install
npm run dev
```

