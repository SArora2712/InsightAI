"""
InsightAI - Shared LLM client wrapper.
Uses generic, provider-agnostic env vars (LLM_API_KEY, LLM_BASE_URL, LLM_MODEL)
per the original design principle: swapping providers is a .env change only.
Falls back to GROQ_-prefixed vars if the generic ones aren't set, for
backward compatibility with any code/.env still using the old names.
"""
import os
import openai
import time
import random

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class LLMCallTracker:
    """
    Tracks LLM call volume for cost/latency visibility and as a circuit
    breaker for Agent v2's loop, which can call the LLM an unbounded
    number of times since it decides its own stopping point.
    """
    def __init__(self):
        self.session_total = 0
        self.query_count = 0

    def reset_query(self):
        """Call once at the start of handling a new user query."""
        self.query_count = 0

    def record_call(self):
        self.query_count += 1
        self.session_total += 1


llm_tracker = LLMCallTracker()
MAX_LLM_CALLS_PER_QUERY = 15
MAX_RETRIES=3
DEFAULT_RETRY_DELAY=2.0

def _can_make_llm_call() -> bool:
    """
    Prevent excessive LLM calls during a single user query.
    """
    if llm_tracker.query_count >= MAX_LLM_CALLS_PER_QUERY:
        print(
            f"[llm_client] Maximum LLM calls per query "
            f"({MAX_LLM_CALLS_PER_QUERY}) reached."
        )
        return False

    return True

def _get_client():
    api_key = (os.getenv("LLM_API_KEY"))

    if not api_key:
        return None, None

    base_url = (os.getenv(
        "LLM_BASE_URL",
        "https://api.groq.com/openai/v1"
    ))

    model = os.getenv(
        "LLM_MODEL",
        "llama-3.1-8b-instant"
    )

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    return client, model

def _get_retry_delay(error: Exception, attempt: int) -> float:
    """
    Determine how long to wait before retrying.

    Priority:
    1. Retry-After header, if provided by provider.
    2. Exponential backoff.
    3. Small random jitter to avoid synchronized retries.
    """

    # Try to read Retry-After from the API response headers.
    try:
        response = getattr(error, "response", None)

        if response is not None:
            headers = getattr(response, "headers", {})

            retry_after = headers.get("retry-after")

            if retry_after:
                return float(retry_after)

    except (ValueError, TypeError):
        pass


    delay = DEFAULT_RETRY_DELAY * (2 ** attempt)

    # Add small jitter.
    jitter = random.uniform(0, 0.5)

    return delay + jitter


def _is_retryable_error(error: Exception) -> bool:
    """
    Return True for errors that may succeed after waiting.
    """

    if isinstance(error, openai.RateLimitError):
        return True

    # Server-side temporary errors.
    if isinstance(error,(openai.InternalServerError,openai.APITimeoutError, openai.APIConnectionError, ),):
        return True

    return False




def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.0, max_tokens: int | None = None) -> str:

    if not _can_make_llm_call():
        raise RuntimeError(
            f"Maximum LLM calls per query "
            f"({MAX_LLM_CALLS_PER_QUERY}) reached."
        )

    client, model = _get_client()
    if client is None:
        return ("[No LLM_API_KEY set — skipping generation. "
                 "Add your key to .env to see actual model output.]")

    kwargs = {}
    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    for attempt in range(MAX_RETRIES + 1):

        try:
            response = client.chat.completions.create(
                model=model, temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                **kwargs,
            )
            llm_tracker.record_call()
            return response.choices[0].message.content

        except Exception as e:

            if not _is_retryable_error(e):
                raise RuntimeError(
                    f"LLM API call failed with "
                    f"{type(e).__name__}: {e}"
                ) from e

            if attempt >= MAX_RETRIES:
                raise RuntimeError(
                    f"LLM API call failed after "
                    f"{MAX_RETRIES} retries: "
                    f"{type(e).__name__}: {e}"
                ) from e

            delay = _get_retry_delay(e, attempt)
            print(f"[llm_client] Temporary API error ({type(e).__name__}). Retrying in {delay:.2f}s (attempt {attempt + 1}/{MAX_RETRIES})...")
            time.sleep(delay)

    return None

def call_llm_with_tools(
    system_prompt: str,
    messages: list[dict],
    tools: list[dict],
    tool_choice: str = "auto",
):

    if not _can_make_llm_call():
        return None

    client, model = _get_client()

    if client is None:
        return None
    base_messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ] + messages

    for attempt in range(MAX_RETRIES + 1):

        try:

            response = client.chat.completions.create(
                model=model,
                temperature=0,
                messages=base_messages,
                tools=tools,
                tool_choice=tool_choice,
            )

            # Count only successful calls.
            llm_tracker.record_call()

            return response.choices[0].message

        except openai.BadRequestError as e:

            # BadRequest is usually caused by an invalid tool call.
            # Retry once with a stronger system prompt.
            print(
                f"[llm_client] Tool-call generation failed with "
                f"tool_choice='{tool_choice}'. "
                f"Retrying with auto: {e}"
            )

            firm_system_prompt = system_prompt + (
                "\n\nIMPORTANT: When calling a tool, output ONLY "
                "the structured tool call. "
                "Do not write reasoning text about which tool to use "
                "in the same turn. "
                "Decide silently, then call exactly one tool."
            )

            firm_messages = [
                {
                    "role": "system",
                    "content": firm_system_prompt,
                }
            ] + messages

            try:

                response = client.chat.completions.create(
                    model=model,
                    temperature=0,
                    messages=firm_messages,
                    tools=tools,
                    tool_choice="auto",
                )

                # Count successful retry.
                llm_tracker.record_call()

                return response.choices[0].message

            except Exception as retry_error:

                print(
                    f"[llm_client] Tool-call retry failed: "
                    f"{type(retry_error).__name__}: "
                    f"{retry_error}"
                )

                return None

        except Exception as e:

            # Retry rate limits and temporary API failures.
            if not _is_retryable_error(e):

                print(
                    f"[llm_client] Unexpected tool-call error: "
                    f"{type(e).__name__}: {e}"
                )

                return None

            if attempt >= MAX_RETRIES:

                print(
                    f"[llm_client] Tool-call failed after "
                    f"{MAX_RETRIES} retries: {e}"
                )

                return None

            delay = _get_retry_delay(e, attempt)

            print(
                f"[llm_client] Temporary tool-call API error "
                f"({type(e).__name__}). "
                f"Retrying in {delay:.2f}s "
                f"(attempt {attempt + 1}/{MAX_RETRIES})..."
            )

            time.sleep(delay)

    return None
