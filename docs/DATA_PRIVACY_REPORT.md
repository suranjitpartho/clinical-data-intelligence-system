# Data Privacy & Compliance Report (Clinical Data)

## 1. Executive Summary
The Clinical Data Intelligence System (CDIS) is architected to prioritize data sovereignty and patient confidentiality. In the healthcare sector, specifically under New Zealand's **Health Information Privacy Code (HIPC)** and international standards like **HIPAA**, the handling of identifiable clinical notes requires stringent controls.

## 2. Privacy-First Embedding Strategy
**Current Implementation:** Local Inference (BGE-M3)
Unlike standard AI applications that transmit data to 3rd party APIs (e.g., OpenAI or Anthropic) for embedding generation, CDIS utilizes local inference during the development and data-cleansing phases.

*   **Zero External Transmission:** 100% of the patient’s clinical notes stay within the local environment.
*   **Vector Isolation:** The generated vectors (`1024-dim`) represent the mathematical meaning of the note but do not contain human-readable text, providing an additional layer of obfuscation.

## 3. Auditability & Compliance
The system includes a dedicated `audit_logs` table that tracks every interaction the AI Agent has with patient data.
*   **Reasoning Traces:** The system stores the "intent" of the AI (e.g., "Finding patients with hypertension").
*   **Tool Usage:** Records whether the AI accessed structured SQL data or the Vector Index.
*   **Access Tracking:** Every query is timestamped to provide a full forensic trail of data access.

## 4. Security Controls
*   **NHI Anonymization:** The system can be configured to use internal UUIDs for all AI processing, with the National Health Index (NHI) only mapped at the final UI presentation layer.
*   **Database Level Security:** PostgreSQL 16 row-level security (RLS) can be implemented on top of this architecture to restrict staff member access based on department-level permissions.
