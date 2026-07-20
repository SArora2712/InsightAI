"""
InsightAI - SQL safety validator.
This is a hard security boundary: no generated SQL reaches the database
without passing through here. Blocks any non-SELECT statement, blocks
statement chaining, and enforces a row limit.
"""
import re

FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE",
    "REPLACE", "ATTACH", "DETACH", "PRAGMA", "VACUUM", "EXEC", "EXECUTE",
]

DEFAULT_ROW_LIMIT = 200


class SQLValidationError(Exception):
    pass


def _strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql


def validate_sql(sql: str) -> str:
    """
    Validate a generated SQL string is safe to execute.
    Returns the (possibly LIMIT-adjusted) SQL if valid, raises SQLValidationError otherwise.
    """
    cleaned = _strip_sql_comments(sql).strip()
    if not cleaned:
        raise SQLValidationError("Empty SQL after stripping comments.")

    # Block statement chaining (e.g. "SELECT ...; DROP TABLE ...")
    # Allow a single optional trailing semicolon.
    body = cleaned[:-1].strip() if cleaned.endswith(";") else cleaned
    if ";" in body:
        raise SQLValidationError("Multiple SQL statements are not allowed.")

    if not re.match(r"^\s*SELECT\b", body, flags=re.IGNORECASE):
        raise SQLValidationError("Only SELECT statements are permitted.")

    upper_body = body.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper_body):
            raise SQLValidationError(f"Forbidden keyword detected: {keyword}")

    # Enforce a row limit if the query doesn't already specify one
    if not re.search(r"\bLIMIT\b", upper_body):
        body = f"{body} LIMIT {DEFAULT_ROW_LIMIT}"

    return body