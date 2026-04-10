# AI Agent Orchestration Workflow

This project uses **LangGraph** to create a non-linear, stateful AI agent capable of clinical reasoning and multi-tool execution.

## The Agent Architecture
Instead of a simple "Prompt -> Answer" chain, the system uses a **State Graph** that manages the conversation flow and tool selection logic.

### 1. The Reasoning Loop
1.  **Classifier Node:** The agent first analyzes the query to decide whether it requires **Structured Data** (SQL) or **Unstructured Context** (RAG/Vector).
2.  **Tool Execution:** 
    *   **SQL Tool:** Writes a PostgreSQL query, executes it, and returns the tabular data.
    *   **Semantic Search Tool:** Converts the query to a vector using the local `BGE-M3` model and performs a similarity search in the `clinical_notes` table.
3.  **Synthesis Node:** The agent takes the raw data (SQL rows or Clinical Notes) and generates a professional medical summary.

### 2. Decision Logic Flow
```mermaid
graph TD
    User([User Query]) --> Classify{Intent Classifier}
    
    Classify -- "How many...?" / "List..." --> SQL[SQL Query Generator]
    Classify -- "Symptoms..." / "History..." --> RAG[Semantic Search Tool]
    
    SQL --> ExecSQL[PostgreSQL Executor]
    RAG --> LocalEmbed[Local Vector Hub]
    
    ExecSQL --> Synth[Response Synthesizer]
    LocalEmbed --> Synth
    
    Synth --> Log[Audit Log / Compliance]
    Log --> Final([Final Answer])
```

## Clinical Guardrails
The agent is designed with specific guardrails to maintain reliability:
*   **Context Isolation:** The agent only has access to the database tools; it cannot call external APIs or hallucinate patient data that doesn't exist.
*   **Traceability:** Every decision (e.g., why a certain tool was chosen) is logged in the `audit_logs` table for clinical review.
*   **Provider Independent:** The logic is abstracted so that the underlying model can be swapped from **Llama 3 (Local)** to **Claude 3 (Cloud)** with a single configuration change.
