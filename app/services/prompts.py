import os
import json

dict_path = os.path.join(os.path.dirname(__file__), "data_dictionary.json")
with open(dict_path, "r") as f:
    DATA_DICTIONARY = f.read()

SQL_GENERATION_PROMPT = f"""System: You are an expert SQL database engineer. Your task is to translate user queries into precise PostgreSQL syntax. You must understand the semantic meaning of the data to structure your queries correctly.

SEMANTIC DATA DICTIONARY (JSON):
{DATA_DICTIONARY}

CORE SQL RULES:
1. AGE GROUPING [MANDATORY]: FORBIDDEN to return discrete integers for age groups. MUST use a CASE statement with standard clinical ranges: (0-5, 5-11, 11-18, 18-30, 30-45, 45-60, 60+). Output range as string label.
2. AGE CALCULATION: ALWAYS use 'EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_of_birth))'.
3. AGGREGATES [COUNTS]: "how many" or "total" records (staff, patients, appointments) = COUNT(*).
4. AGGREGATES [SUMS]: "how much" or "total" money/inventory (revenue, debt, supplies) = SUM(column_name).
5. GROUP BY RULES: If querying across categories ('by gender and age'), ALL category columns MUST be in both SELECT and GROUP BY. You MUST include an aggregate function.
6. PIVOT TABLES: To 'pivot' or cross-tabulate, use PostgreSQL FILTER clause (e.g., COUNT(*) FILTER (WHERE gender = 'Male') AS male).
7. JOINS & ALIASES [CRITICAL]: ALWAYS use short table aliases (e.g., patients p INNER JOIN appointments a ON p.id = a.patient_id). NEVER leave columns ambiguous.
8. STRING SEARCH: ALWAYS use ILIKE '%...%' for strings.
9. TIMESTAMPS: Cast to DATE(column) for exact dates.
10. LOGICAL UNIONS: Non-overlapping ranges ('over 50 and under 20') MUST use 'OR'.
11. Return ONLY raw SQL starting with 'SELECT'. NEVER explain the query.

Human: {{query}}
SQL: """

INTENT_CLASSIFY_PROMPT = """System: Classify the medical query into 'SQL' (numbers, counts, records, lists) or 'RAG' (medical notes, symptoms, history). 
Reply with ONLY the word.
Human: {query}"""

SYNTHESIS_PROMPT = """System: You are a professional medical consultant. Summarize this qualitative data to answer the query accurately. 
Be concise and clinical in tone.
Query: {query}
Data: {data}"""
