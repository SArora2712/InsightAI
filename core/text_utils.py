import re
from core.llm_client import call_llm


def strip_inline_code(text: str) -> str:
    """Remove Markdown inline-code backticks from generated prose.

    Flattens short, single-line code spans (e.g. `` `448.4M` ``) so figures
    use the surrounding font instead of Streamlit's monospace code styling.
    Only spans up to 64 chars on a single line are flattened: a closing
    backtick far away (or across a newline) could otherwise match an early
    opening backtick and swallow real prose in between. Any remaining stray
    backticks are dropped so a lone backtick can never affect rendering.
    """
    if not text:
        return text
    cleaned = re.sub(r"`([^`\n]{1,64})`", r"\1", text)
    return cleaned.replace("`", "")


def multiplication_mark(text: str) -> str:
    """Render lone arithmetic asterisks as the multiplication sign (×).

    Generated prose writes formulas like "37.97 * 0.10 = 41.67". A raw "*"
    passed through Markdown risks being parsed as an emphasis delimiter, and
    backslash-escaping it ("\\*") leaks a visible backslash on some renderers.
    Substituting the × glyph is immune to Markdown parsing and reads naturally.
    Bold markers ("**text**") and longer asterisk runs are preserved untouched.
    """
    if not text:
        return text
    return re.sub(r"(?<!\*)\*(?!\*)", "×", text)


def clean_prose(text: str) -> str:
    """Prepare generated AI prose for safe, consistent Markdown rendering.

    Flattens inline-code backticks (protecting against code-span styling and
    backtick-pair prose deletion) and converts lone arithmetic asterisks to
    the multiplication sign, which is immune to emphasis parsing. Never emits
    backslash escapes, so "\*" can never appear in rendered output.

    Use at every point where an LLM answer is passed to st.markdown. For
    paths that HTML-escape into an unsafe_allow_html block, use
    strip_inline_code() only (asterisks already render literally there).
    """
    if not text:
        return text
    return multiplication_mark(strip_inline_code(text))


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