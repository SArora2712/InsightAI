"""
InsightAI - Tool schemas (OpenAI function-calling format) for the agentic loop.

Each tool description tells the LLM when the tool should be used.
The actual Python implementations are provided separately by
agents.agentic.agent.build_agent_tools().
"""

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "query_sales_database",
            "description": (
                "Query Northwind Traders' structured sales database for "
                "quantitative business questions, including revenue, order "
                "counts, top customers, top products, employees, category "
                "performance, regional performance, and shipping data. "
                "Use this tool only for information that can be answered "
                "from Northwind's sales database."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": (
                            "The specific natural-language business question "
                            "to answer using the Northwind sales database."
                        ),
                    }
                },
                "required": ["question"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "Search the live internet ONLY for current external "
                "information that is directly relevant to Northwind Traders' "
                "business, sales operations, market conditions, competitors, "
                "economic conditions, or regulatory environment. "
                "Do NOT use this tool for general trivia, unrelated people, "
                "or unrelated current events."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": (
                            "A specific current external business question "
                            "that is directly relevant to Northwind Traders."
                        ),
                    }
                },
                "required": ["question"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_internal_documents",
            "description": (
                "Search Northwind Traders' internal company reports and "
                "documents for qualitative context, narrative analysis, "
                "business commentary, policies, and information that is "
                "not captured as raw numbers in the sales database."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": (
                            "The specific question to answer using "
                            "Northwind Traders' internal documents."
                        ),
                    }
                },
                "required": ["question"],
                "additionalProperties": False,
            },
        },
    },
]