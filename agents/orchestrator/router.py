"""
InsightAI - Orchestrator routing logic.

One LLM call classifies which data-source agent(s) are relevant to a
question. Multiple agents can be selected when a question requires
cross-source analysis.

Examples:
- SQL only: structured Northwind sales data
- Document RAG only: internal reports and policies
- Web only: current external information
- Multiple: internal sales data + current market context
- Empty list: out-of-scope question
"""

import json
import re

from core.llm_client import call_llm


VALID_AGENTS = {
    "document_rag",
    "sql",
    "web",
}


ROUTER_SYSTEM_PROMPT = """
You are the routing classifier for InsightAI, a business analyst AI system
specialized in Northwind Traders.

Your job is to determine which specialized data-source agents are needed
to answer the user's question.

Available agents:

- "document_rag":
  Use for Northwind Traders internal company documents, reports,
  policies, qualitative business commentary, and internal context.

- "sql":
  Use for Northwind Traders structured business and sales data, including
  customers, orders, products, employees, categories, suppliers,
  shippers, quantities, revenue, and other database information.

- "web":
  Use for current external information directly relevant to Northwind
  Traders, including current events, economic conditions, interest rates,
  Federal Reserve policy, inflation, competitors, regulations,
  industry trends, and market context.

A question may require MORE THAN ONE agent.

Examples:

Question:
"What was total revenue by product category?"
Return:
["sql"]

Question:
"What does the internal report say about revenue?"
Return:
["document_rag"]

Question:
"What is the current Federal Reserve interest-rate policy?"
Return:
["web"]

Question:
"How might current interest rates affect Northwind Traders' sales?"
Return:
["web"]

Question:
"Compare the revenue in our database with the internal report."
Return:
["sql", "document_rag"]

Question:
"How did our sales perform, and how might current inflation affect
future sales?"
Return:
["sql", "web"]

Question:
"What was our revenue in Q3 2023?"
Return:
["sql"]

Question:
"What was our revenue in 2023 compared with 2022?"
Return:
["sql"]

Question:
"What does our internal report say about our 2023 revenue decline?"
Return:
["document_rag"]

Question:
"What was our revenue in Q3 2023, and how did inflation affect sales during that quarter?"
Return:
["sql", "web"]

Question:
"What was our revenue in Q3 2023, according to our internal reports?"
Return:
["sql", "document_rag"]


IMPORTANT OUT-OF-SCOPE RULE:

Return an EMPTY JSON ARRAY [] when the question has no plausible
business-analysis relevance to Northwind Traders.

Examples of out-of-scope questions:

"What is programming?"
"What is Python?"
"Explain quantum physics."
"Write a poem."
"Tell me a joke."
"Help me debug my code."
"What is the capital of France?"
"How to train models?"                
"What is photosynthesis?"   

For these questions, return exactly:

[]

Do NOT route out-of-scope questions to SQL, document_rag, or web.

IMPORTANT ROUTING PRIORITY RULES:

1. If the user asks for a specific Northwind Traders metric, historical
   business result, sales figure, revenue, order count, product performance,
   customer data, or other structured company data, route to "sql" ONLY,
   unless the question explicitly asks for information from internal reports.

2. If the question asks about what internal reports, documents, or company
   analysis say, route to "document_rag".

3. If the question asks about CURRENT external information, such as current
   inflation, current interest rates, Federal Reserve policy, current
   economic conditions, competitors, regulations, or market trends, route
   to "web".

4. Use multiple agents ONLY when the question genuinely requires information
   from multiple sources. Do not add "web" merely because a historical date,
   quarter, year, or economic concept appears in the question.

5. A historical company metric such as:
   "What was our revenue in Q3 2023?"
   is an SQL question, NOT a web question.

6. If SQL cannot answer a question because the database has no matching data,
   do not automatically route to web. The system should report that the
   requested internal metric could not be determined from the available
   database unless the user explicitly asks for external context.

Economic and market-context questions are IN SCOPE when they could
reasonably help analyze Northwind Traders' business, even if the question
does not explicitly mention Northwind Traders. However, this rule does NOT
override the source-specific routing rules above.



Return ONLY a valid JSON array containing zero or more of:

"document_rag"
"sql"
"web"

Do not return explanations.
Do not use Markdown.
Do not wrap the JSON in code fences.
"""


def _parse_agent_list(raw_output: str) -> list[str]:
    """
    Parse and validate the LLM router response.

    An empty list [] is a VALID result and means the question
    is out of scope.

    If the LLM returns malformed output, use a conservative
    fallback rather than silently treating the question as
    out of scope.
    """

    if not raw_output:
        return list(VALID_AGENTS)

    text = raw_output.strip()

    # Remove Markdown code fences if the model accidentally adds them.
    fence_match = re.search(
        r"```(?:json)?\s*(.*?)```",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if fence_match:
        text = fence_match.group(1).strip()

    try:
        parsed = json.loads(text)

        if not isinstance(parsed, list):
            raise ValueError("Router output is not a JSON array.")

        # IMPORTANT:
        # [] is valid and means OUT OF SCOPE.
        agents = [
            agent
            for agent in parsed
            if agent in VALID_AGENTS
        ]

        return agents

    except (json.JSONDecodeError, ValueError, TypeError):

        print(
            "[router] WARNING: Invalid LLM routing output. "
            "Falling back to all agents."
        )
        print(f"[router] Raw output: {raw_output!r}")

        # Fail-open fallback for malformed router output.
        # This is different from a legitimate [] response.
        return list(VALID_AGENTS)


def route_question(question: str) -> list[str]:
    """
    Return the list of specialized agents required for the question.

    Returns:
        ["sql"]
        ["document_rag"]
        ["web"]
        ["sql", "document_rag"]
        []
        
    An empty list means the question is out of scope.
    """

    try:
        raw_output = call_llm(ROUTER_SYSTEM_PROMPT, question)
    except Exception as e:
        print(
            f"[router] ERROR: LLM router call failed ({type(e).__name__}: {e}). "
            "Falling back to all agents."
        )
        return list(VALID_AGENTS)
    print(f"[router] DEBUG raw_output: {raw_output!r}")
    if raw_output is None:
        print(
            "[router] WARNING: LLM returned None. "
            "Falling back to all agents."
        )
        return list(VALID_AGENTS)

    if (
        raw_output.startswith("[No")
        and "API_KEY" in raw_output
    ):
        print(
            "[router] WARNING: No LLM API key available. "
            "Falling back to all agents for testability."
        )
        return list(VALID_AGENTS)

    return _parse_agent_list(raw_output)