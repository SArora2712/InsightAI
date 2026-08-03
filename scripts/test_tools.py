# test_tools.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.llm_client import call_llm_with_tools
from agents.agentic.tools_schema import TOOLS_SCHEMA

messages = [
    {
        "role": "user",
        "content": "What are the top 5 customers by revenue?"
    }
]

message = call_llm_with_tools(
    """
    You are a Northwind Traders business analyst.

    If the user asks about Northwind sales data,
    use the query_sales_database tool.
    """,
    messages,
    TOOLS_SCHEMA,
)

print("CONTENT:")
print(message.content)

print("\nTOOL CALLS:")
print(message.tool_calls)