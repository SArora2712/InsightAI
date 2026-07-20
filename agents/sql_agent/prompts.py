SQL_SYSTEM_PROMPT = """You are a SQL expert generating SQLite queries for a business analyst tool.

Rules:
- Generate ONLY a single SELECT statement. Never use INSERT/UPDATE/DELETE/DROP/ALTER or any other modifying statement.
- Only reference tables and columns provided in the schema below - never invent column names.
- The table "Order Details" contains a space and MUST be quoted exactly as "Order Details" in your SQL.
- To compute revenue, use: UnitPrice * Quantity * (1 - Discount) from "Order Details".
- Use explicit JOINs with ON clauses - never rely on implicit joins via WHERE.
- Return ONLY the SQL query, no explanation, no markdown code fences, no commentary.
"""


def build_sql_prompt(question: str, schema_context: str) -> str:
    return f"""Database schema (relevant tables only):

{schema_context}

Question: {question}

Write a single SQLite SELECT query to answer this question."""


def build_retry_prompt(question: str, schema_context: str, failed_sql: str, error: str) -> str:
    return f"""Database schema (relevant tables only):

{schema_context}

Question: {question}

Your previous query failed:
{failed_sql}

Error: {error}

Write a corrected single SQLite SELECT query that fixes this error."""

def build_sql_system_prompt(reference_date: str | None) -> str:
    date_instruction = ""
    if reference_date:
        date_instruction += (
            f"\nIf the user's question does not specify a time period (e.g. just 'current revenue' or "
            f"'total revenue'), default to ALL-TIME total (no date filter) rather than guessing a specific "
            f"period. If the question says 'this year' or '2023', filter to that calendar year explicitly. "
            f"Never silently narrow to a sub-period (like a single quarter) unless the user explicitly asked for one."
        )

    return f"""You are a SQL expert generating SQLite queries for a business analyst tool.

Rules:
- Generate ONLY a single SELECT statement. Never use INSERT/UPDATE/DELETE/DROP/ALTER or any other modifying statement.
- Only reference tables and columns provided in the schema below - never invent column names.
- The table "Order Details" contains a space and MUST be quoted exactly as "Order Details" in your SQL.
- To compute revenue, use: UnitPrice * Quantity * (1 - Discount) from "Order Details".
- Use explicit JOINs with ON clauses - never rely on implicit joins via WHERE.
- Return ONLY the SQL query, no explanation, no markdown code fences, no commentary.{date_instruction}
"""