# Architectural Decision Records (ADR)

This document outlines the key technical decisions made during the development of the Clinical Data Intelligence System (CDIS).

## 1. Database: PostgreSQL 16 + pgvector
**Decision:** Use PostgreSQL with the `pgvector` extension for both relational and vector data.
**Rationale:** 
*   **Unified System:** Storing clinical notes and their semantic vectors in the same database as appointments and billing prevents "data drift" and simplifies backups.
*   **Performance:** `pgvector` supports HNSW (Hierarchical Navigable Small World) indexing, allowing for sub-second retrieval across millions of vectors.
*   **Relational Context:** Healthcare data is deeply relational. We can easily filter search results by `doctor_id` or `department_id` using standard SQL joins before performing vector similarity.

## 2. Primary Keys: UUID v4
**Decision:** Use UUIDs instead of auto-incrementing integers for all primary keys.
**Rationale:**
*   **Security:** Integers (1, 2, 3...) allow for "Insecure Direct Object Reference" (IDOR) attacks where a malicious user could guess the ID of another patient. UUIDs are non-guessable.
*   **Scalability:** UUIDs allow for distributed systems and offline data generation without risk of ID collisions during synchronization.

## 3. Local Embedding Generation (BGE-M3)
**Decision:** Use `BAAI/bge-m3` via `sentence-transformers` for local development.
**Rationale:**
*   **Patient Privacy:** In clinical settings, patient notes are highly sensitive. Generating embeddings locally on the MacBook M5 ensures no clinical data is transmitted to 3rd party cloud providers during development.
*   **Cost:** Processing 5,000+ records via cloud APIs (OpenAI) can be costly during the R&D phase. Local processing is free and utilizes the M5's neural engine.

## 4. Framework: FastAPI (Asynchronous)
**Decision:** Use FastAPI for the REST interface.
**Rationale:**
*   **Concurrency:** Handling many AI agent requests simultaneously requires non-blocking I/O.
*   **Type Safety:** Pydantic models ensure that clinical data (like NHI numbers or medication dosages) are strictly validated before hitting the database.
