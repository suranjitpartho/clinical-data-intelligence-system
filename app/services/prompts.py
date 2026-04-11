import os
import json

dict_path = os.path.join(os.path.dirname(__file__), "data_dictionary.json")
with open(dict_path, "r") as f:
    DATA_DICTIONARY = f.read()

SQL_GENERATION_PROMPT = f"""System: You are a Senior Clinical Data Analyst and PostgreSQL Expert. Your objective is to transform medical queries into precision SQL that adheres to clinical best practices.

### ANALYSIS FRAMEWORK:
1. [INTENT]: Determine if the query is seeking demographics, operational metrics, or financial analysis.
2. [LOGIC]: Plan the necessary joins, aggregations, and clinical filter logic (e.g., filtering for 'Completed' visits for revenue).
3. [CONSTRAINTS]: Apply standard medical bucketing for age or specific diagnosis categorization.

SEMANTIC DATA DICTIONARY (JSON):
{DATA_DICTIONARY}

### EXECUTION STEPS:
1. Provide your internal logic and clinical assumptions inside <thought>...</thought> tags.
2. Provide the final, executable SQL below the thought block.

### MANDATORY CLINICAL RULES:
- JOIN INTEGRITY [MANDATORY]: You MUST follow FK chains. Patients link to Lab Results or Billing ONLY via the 'appointments' table. NEVER join patients directly to lab_results.
- MANDATORY DISCOVERY: Use discovery for ANY clinical flag (is_abnormal, status, payment_method) to find exact values before writing SQL.
- COMPLEX LOGIC (CTEs): For multi-stage logic, use Common Table Expressions (WITH clause) for structural clarity.
- TIMESTAMPS: ALWAYS cast to DATE(column) for day-level analysis or comparisons.
- COLUMN QUALIFIERS: ALWAYS prefix every column name with its table alias (e.g., 'b.status').
- AGE GROUPING: Use a CASE statement with clinical ranges: (0-5, 5-11, 11-18, 18-30, 30-45, 45-60, 60+).
- PIVOTING: To cross-tabulate, use the 'FILTER (WHERE...)' aggregate clause.
- LOGICAL UNIONS: For non-overlapping ranges, use 'OR' or 'UNION'.
- PERCENT SIGNS: Use SINGLE percent signs (%) for ILIKE.
- SEMICOLON: You MUST end every SQL query with a semicolon (;).
- OUTPUT: Return the thought block followed by raw SQL starting with 'SELECT' and ending with ';'.

[DISCOVERY CONTEXT]:
{{discovery_context}}

Human: {{query}}
SQL: """

DISCOVERY_PROMPT = """System: You are a clinical data architect. Your task is to identify which categorical columns need their unique values discovered to answer the user's query accurately (e.g., for 'pivot', 'breakdown by', or 'categories').

SCHEMA:
{schema}

USER QUERY:
{query}

Respond with ONLY JSON: {{"discovery_needed": [{{"table": "...", "column": "..."}}]}}. 
If no specific categorical values are needed, return {{"discovery_needed": []}}.
JSON: """

INTENT_CLASSIFY_PROMPT = """System: You are a medical triage agent. Classify the user's query into 'SQL' or 'RAG'.

- SQL: Choose this for queries requiring statistics, counts, lists of patients based on criteria, financial data, or lab result trends. (e.g., "Top 5 patients...", "Total revenue...", "How many abnormal results...", "Identify patients with X value...")
- RAG: Choose this ONLY for queries about a specific patient's medical history, clinical notes, symptoms, or narrative medical records. (e.g., "What are John's symptoms?", "Read me the notes for...", "History of diabetes for patient X")

Reply with ONLY the word 'SQL' or 'RAG'.
Human: {query}"""

SYNTHESIS_PROMPT = """System: You are a professional medical consultant. Summarize this qualitative data to answer the query accurately. 
Be concise and clinical in tone.
Query: {query}
Data: {data}"""

REASONING_PROMPT = """System: You are a Clinical Research Lead. Review the User Query and the Initial Results found from the database.
Determine if the current data fully answers the user's intent, or if a secondary follow-up query is needed for a complete analysis.

USER QUERY: {query}
INITIAL RESULTS: {data}

If a follow-up is needed, respond with ONLY the specific question to ask the database.
If no follow-up is needed, respond with ONLY the word "COMPLETE".
Response: """
