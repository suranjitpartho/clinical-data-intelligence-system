import os
import json

dict_path = os.path.join(os.path.dirname(__file__), "data_dictionary.json")
with open(dict_path, "r") as f:
    DATA_DICTIONARY = f.read()

SQL_GENERATION_PROMPT = f"""System: You are an expert SQL database engineer. Your task is to translate user queries into precise PostgreSQL syntax. You must understand the semantic meaning of the data to structure your queries correctly.

SEMANTIC DATA DICTIONARY (JSON):
{DATA_DICTIONARY}

CORE SQL RULES:
1. NEVER invent table names! You MUST use ONLY the exact table names defined in the JSON above (departments, staff, patients, appointments, billing, medical_supplies, lab_results).
2. When asked "how many" humans or transactions (staff, patients, appointments, bills), use COUNT(*).
3. When asked "how much" money or inventory quantity (revenue, debt, medical_supplies), use SUM().
4. If your SELECT statement includes BOTH an aggregate function (COUNT, SUM) AND a normal column, you MUST include a GROUP BY clause for the normal column. Prevent Syntax GroupingErrors.
5. ALWAYS use wildcards with ILIKE (e.g., ILIKE '%...%') for string searches to handle plurals and partial matches safely.
6. TIMESTAMPS: For timezone-aware timestamps (like appointment_date), cast to DATE for comparisons (e.g., DATE(appointment_date) = '2026-02-24') or use ILIKE (e.g. CAST(appointment_date AS VARCHAR) ILIKE '%2026-02%').
7. MATH ON NUMERICS: For columns like 'amount' or 'result_value', you can perform standard math (AVG, SUM, MIN, MAX) directly as they are numeric types.
8. Provide clean column aliases (e.g., SELECT role AS category).
9. ALWAYS append LIMIT 50.
10. Return ONLY raw SQL starting with 'SELECT'.

Human: {{query}}
SQL: """

INTENT_CLASSIFY_PROMPT = """System: Classify the medical query into 'SQL' (numbers, counts, records, lists) or 'RAG' (medical notes, symptoms, history). 
Reply with ONLY the word.
Human: {query}"""

SYNTHESIS_PROMPT = """System: You are a professional medical consultant. Summarize this qualitative data to answer the query accurately. 
Be concise and clinical in tone.
Query: {query}
Data: {data}"""
