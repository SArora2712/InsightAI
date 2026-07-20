
from core.llm_client import call_llm


def ensure_prose(answer: str, question: str) -> str:
    """
    Safety net: if the model returned raw JSON/data instead of prose (a
    regression risk from over-literal "don't add opinions" instructions),
    regenerate once as clean text.
    """
    if answer and answer.strip().startswith(("{", "[")):
        return call_llm(
            "Rewrite the following as clear, natural prose sentences for a business user - "
            "do not use JSON or code formatting. Do not add any opinions or recommendations "
            "beyond what's stated.",
            f"Question: {question}\n\nRaw data to rewrite as prose:\n{answer}",
        )
    return answer