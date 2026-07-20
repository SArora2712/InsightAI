"""
InsightAI - Web Agent answer synthesis.
Takes raw Tavily results and produces a synthesized, attributable answer
via the LLM - never copy-pasting source snippets verbatim.
"""

from core.llm_client import call_llm

SYNTHESIS_SYSTEM_PROMPT = """You are a business analyst summarizing live web search results.

Rules:
- Write the answer in your own words - never copy sentences verbatim from the source content.
- Base your answer ONLY on the provided search results. If they don't answer the question, say so explicitly - do not fill gaps from your own general knowledge.
- Be concise: 2-4 sentences unless the question clearly needs more detail.
- Do not fabricate statistics, dates, or figures not present in the results.
"""


def _format_results_for_prompt(results: list[dict]) -> str:
    blocks = []
    for i, r in enumerate(results, 1):
        blocks.append(f"[Source {i}] {r['title']} ({r['url']})\n{r['content'][:800]}")
    return "\n\n".join(blocks)


def synthesize_answer(question: str, results: list[dict]) -> str:
    if not results:
        return "No relevant web search results were found for this question."

    context = _format_results_for_prompt(results)
    prompt = f"""Search results:

{context}

Question: {question}

Write a synthesized answer based only on these results."""

    return call_llm(SYNTHESIS_SYSTEM_PROMPT, prompt)