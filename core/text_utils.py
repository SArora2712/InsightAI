import re
from core.llm_client import call_llm


def ensure_prose(answer: str, question: str) -> str:
    """
    Safety net: if the model returned raw JSON/data instead of prose (a
    regression risk from over-literal "don't add opinions" instructions),
    regenerate once as clean text. Checks both bare JSON and JSON wrapped
    in a markdown code fence, since the model can produce either.
    """
    if not answer:
        return answer

    stripped = answer.strip()
    fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", stripped, flags=re.DOTALL)
    check_text = fence_match.group(1).strip() if fence_match else stripped

    if check_text.startswith(("{", "[")):
        return call_llm(
            "Rewrite the following as clear, natural prose sentences for a business user - "
            "do not use JSON or code formatting. Do not add any opinions or recommendations "
            "beyond what's stated.",
            f"Question: {question}\n\nRaw data to rewrite as prose:\n{check_text}",
        )
    return answer