SQL_SYSTEM_PROMPT = """You are a SQL expert generating SQLite queries for a business analyst tool.

Rules:
- Generate ONLY a single SELECT statement. Never use INSERT/UPDATE/DELETE/DROP/ALTER or any other modifying statement.
- Only reference tables and columns provided in the schema below - never invent column names.
- The table "Order Details" contains a space and MUST be quoted exactly as "Order Details" in your SQL.
- To compute revenue, use: UnitPrice * Quantity * (1 - Discount) from "Order Details".
- Use explicit JOINs with ON clauses - never rely on implicit joins via WHERE.

SQLite date rules:
- This database uses SQLite syntax.
- NEVER use YEAR(), MONTH(), DATE_FORMAT(), or other MySQL-specific date functions.
- To extract a year from a date, use strftime('%Y', date_column).
- To extract a month from a date, use strftime('%m', date_column).
- To extract a day from a date, use strftime('%d', date_column).
- For calendar-year filtering, use a date range when possible, for example:
  date_column >= '2023-01-01' AND date_column < '2024-01-01'.
- If using strftime() for year filtering, use:
  strftime('%Y', date_column) = '2023'.

Return ONLY the SQL query, no explanation, no markdown code fences, no commentary.
"""


def build_sql_prompt(question: str, schema_context: str) -> str:
    return f"""Database schema (relevant tables only):

{schema_context}

Question: {question}

Write a single SQLite SELECT query to answer this question."""


def build_retry_prompt(
    question: str,
    schema_context: str,
    failed_sql: str,
    error: str
) -> str:
    return f"""Database schema (relevant tables only):

{schema_context}

Question: {question}

Your previous query failed:
{failed_sql}

Error: {error}

Write a corrected single SQLite SELECT query that fixes this error.

Remember:
- The database is SQLite.
- Do not use YEAR(), MONTH(), DATE_FORMAT(), or other MySQL-specific functions.
- Use SQLite-compatible date functions such as strftime() or explicit date ranges.

Return ONLY the corrected SQL query."""


def build_sql_system_prompt(reference_date: str | None) -> str:
    date_instruction = ""
    if reference_date:
        date_instruction = (
            f"If the user asks for 'total revenue' without specifying a time period,  calculate all-time revenue."
            f"\nIf the user asks for \"current revenue\" or \"latest revenue\","
            f"use the most recent available reporting period in the database."
            f"\nNever describe an all-time total as \"current revenue\"."
            f"period. If the question says 'this year' or '2023', filter to "
            f"that calendar year explicitly. Never silently narrow to a "
            f"sub-period (like a single quarter) unless the user explicitly "
            f"asked for one."
        )

    return f"""You are a SQL expert generating SQLite queries for a business analyst tool.

Rules:
- Generate ONLY a single SELECT statement. Never use INSERT/UPDATE/DELETE/DROP/ALTER or any other modifying statement.
- Only reference tables and columns provided in the schema below - never invent column names.
- The table "Order Details" contains a space and MUST be quoted exactly as "Order Details" in your SQL.
- To compute revenue, use: UnitPrice * Quantity * (1 - Discount) from "Order Details".
- Use explicit JOINs with ON clauses - never rely on implicit joins via WHERE.
- When a question asks about "employees", "sales reps", "top performers", or similar - referring to \
PEOPLE - group by individual employee (EmployeeID, or FirstName || ' ' || LastName), NEVER by Title/role. \
Grouping by Title silently combines multiple different people who share that job title into one row, \
which misrepresents who is actually being asked about. Only group by Title when the question explicitly \
asks about roles or positions, not individual people.
- When identifying individual employees, ALWAYS include their name (e.g. e.FirstName || ' ' || \
e.LastName AS EmployeeName) in the SELECT, not just EmployeeID - a bare ID number is not useful to a \
business user reading the final answer.
PEOPLE - group by individual employee (EmployeeID, or FirstName || ' ' || LastName), NEVER by Title/role. \
Grouping by Title silently combines multiple different people who share that job title into one row, \
which misrepresents who is actually being asked about. Only group by Title when the question explicitly \
asks about roles or positions, not individual people.

SQLite date rules:
- This database uses SQLite syntax.
- NEVER use YEAR(), MONTH(), DATE_FORMAT(), or other MySQL-specific date functions.
- To extract a year from a date, use strftime('%Y', date_column).
- To extract a month from a date, use strftime('%m', date_column).
- To extract a day from a date, use strftime('%d', date_column).
- For calendar-year filtering, prefer explicit date ranges when possible.
- Example: date_column >= '2023-01-01' AND date_column < '2024-01-01'.
- Alternatively, use strftime('%Y', date_column) = '2023'.
- SQLite does NOT support the YEAR() function. NEVER use YEAR().
- For calendar-year filtering, use explicit date ranges.
- For Q1, use >= 'YYYY-01-01' AND < 'YYYY-04-01'.
- For Q2, use >= 'YYYY-04-01' AND < 'YYYY-07-01'.
- For Q3, use >= 'YYYY-07-01' AND < 'YYYY-10-01'.
- For Q4, use >= 'YYYY-10-01' AND < 'YYYY+1-01-01'.
- When the user asks whether a reported increase, decrease, or decline
  is reflected in actual sales data, compare the relevant periods directly.
- Do not use an all-time revenue total to prove a yearly or quarterly trend.
- For comparison questions, return the revenue for each relevant period
  so the change can be determined.
- If the requested period extends beyond the database's maximum available
  date, clearly indicate that the result is only a partial period.

- IMPORTANT: Q3 means ONLY July 1 through September 30.
- For "Q3 2023", the exact filter MUST be:
  OrderDate >= '2023-07-01' AND OrderDate < '2023-10-01'.
- NEVER use '2024-01-01' as the end date for Q3 2023.
- Q4 2023 is a separate period: OrderDate >= '2023-10-01' AND OrderDate < '2024-01-01'.
    
  Return ONLY the SQL query, no explanation, no markdown code fences, no commentary.{date_instruction}
"""