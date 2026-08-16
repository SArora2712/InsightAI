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
import streamlit as st

from core.envutil import read_env
from core.logging_util import get_logger

logger = get_logger("core.llm_client")

load_dotenv()


class LLMCallTracker:
    """
    Tracks LLM call volume + tokens for cost/latency visibility and as a
    circuit breaker for Agent v2's loop, which can call the LLM an
    unbounded number of times since it decides its own stopping point.
    """
    def __init__(self):
        self.session_total = 0
        self.query_count = 0
        self.query_tokens = 0
        self.session_tokens = 0

    def reset_query(self):
        """Call once at the start of handling a new user query."""
        self.query_count = 0
        self.query_tokens = 0

    def record_call(self, tokens: int = 0):
        self.query_count += 1
        self.session_total += 1
        if tokens:
            self.query_tokens += tokens
            self.session_tokens += tokens

    def snapshot(self) -> dict:
        """Point-in-time usage summary for the monitoring dashboard."""
        return {
            "query_count": self.query_count,
            "session_total": self.session_total,
            "query_tokens": self.query_tokens,
            "session_tokens": self.session_tokens,
        }


llm_tracker = LLMCallTracker()
MAX_LLM_CALLS_PER_QUERY = 15
MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 2.0

# Exact-match TTL cache for LLM responses. Keyed by the full prompt pair, so it
# only ever returns a cached result for an identical repeat call (e.g. a re-run
# of the same script or a repeated "Generate report"), never for a novel query.
# Returning from cache also skips the per-query call budget, which is the point
# of the cache - it saves both cost and the circuit-breaker headroom.
_LLM_CACHE: dict = {}
_LLM_CACHE_TTL_SECONDS = 300
_LLM_CACHE_MAX_ENTRIES = 128


def _llm_cache_get(key: tuple) -> str | None:
    cached = _LLM_CACHE.get(key)
    if cached is None:
        return None
    ts, value = cached
    if time.time() - ts < _LLM_CACHE_TTL_SECONDS:
        return value
    _LLM_CACHE.pop(key, None)
    return None


def _effective_limit() -> int:
    """Higher call budget while generating the Executive Report."""
    if st.session_state.get("is_generating_report"):
        return 40
    return MAX_LLM_CALLS_PER_QUERY


def _can_make_llm_call() -> bool:
    """
    Prevent excessive LLM calls during a single user query.
    Allows a higher limit when generating the Executive Report.
    """
    limit = _effective_limit()

    if llm_tracker.query_count >= limit:
        logger.warning(
            "Maximum LLM calls per query (%s) reached "
            "(query_count=%s, session_total=%s).",
            limit, llm_tracker.query_count, llm_tracker.session_total,
        )
        return False

    return True


def _get_client():
    api_key = read_env("LLM_API_KEY")

    if not api_key:
        return None, None

    base_url = read_env(
        "LLM_BASE_URL",
        "https://api.groq.com/openai/v1"
    )

    model = read_env(
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
    jitter = random.uniform(0, 0.5)
    return delay + jitter


def _is_retryable_error(error: Exception) -> bool:
    """Return True for errors that may succeed after waiting."""
    if isinstance(error, openai.RateLimitError):
        return True

    if isinstance(error, (openai.InternalServerError, openai.APITimeoutError, openai.APIConnectionError)):
        return True

    return False


def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.0,
    max_tokens: int | None = None,
) -> str:

    if not _can_make_llm_call():
        raise RuntimeError(
            f"Maximum LLM calls per query "
            f"({MAX_LLM_CALLS_PER_QUERY}) reached."
        )

    client, model = _get_client()
    if client is None:
        return (
            "[No LLM_API_KEY set — skipping generation. "
            "Add your key to .env to see actual model output.]"
        )

    cache_key = (system_prompt, user_prompt, temperature, max_tokens)
    cached_value = _llm_cache_get(cache_key)
    if cached_value is not None:
        logger.debug("Returning cached LLM response (exact-match hit).")
        return cached_value

    kwargs = {}
    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                **kwargs,
            )
            content = response.choices[0].message.content
            usage = getattr(response, "usage", None)
            tokens = (usage.total_tokens if usage is not None else 0) or 0
            llm_tracker.record_call(tokens)
            logger.debug(
                "LLM response model=%s tokens=%s query_calls=%s/%s",
                model, tokens, llm_tracker.query_count, _effective_limit(),
            )
            _LLM_CACHE[cache_key] = (time.time(), content)
            if len(_LLM_CACHE) > _LLM_CACHE_MAX_ENTRIES:
                _LLM_CACHE.clear()
            return content

        except Exception as e:
            if not _is_retryable_error(e):
                raise RuntimeError(
                    f"LLM API call failed with {type(e).__name__}: {e}"
                ) from e

            if attempt >= MAX_RETRIES:
                raise RuntimeError(
                    f"LLM API call failed after {MAX_RETRIES} retries: "
                    f"{type(e).__name__}: {e}"
                ) from e

            delay = _get_retry_delay(e, attempt)
            logger.warning(
                "Temporary API error (%s). Retrying in %.2fs "
                "(attempt %s/%s)...",
                type(e).__name__, delay, attempt + 1, MAX_RETRIES,
            )
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
        {"role": "system", "content": system_prompt}
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
            llm_tracker.record_call()
            return response.choices[0].message

        except openai.BadRequestError as e:
            logger.warning(
                "Tool-call generation failed with tool_choice=%r. "
                "Retrying with auto: %s", tool_choice, e,
            )

            firm_system_prompt = system_prompt + (
                "\n\nIMPORTANT: When calling a tool, output ONLY "
                "the structured tool call. "
                "Do not write reasoning text about which tool to use "
                "in the same turn. "
                "Decide silently, then call exactly one tool."
            )

            firm_messages = [
                {"role": "system", "content": firm_system_prompt}
            ] + messages

            try:
                response = client.chat.completions.create(
                    model=model,
                    temperature=0,
                    messages=firm_messages,
                    tools=tools,
                    tool_choice="auto",
                )
                llm_tracker.record_call()
                return response.choices[0].message

            except Exception as retry_error:
                logger.error(
                    "Tool-call retry failed: %s: %s",
                    type(retry_error).__name__, retry_error,
                )
                return None

        except Exception as e:
            if not _is_retryable_error(e):
                logger.error(
                    "Unexpected tool-call error: %s: %s",
                    type(e).__name__, e,
                )
                return None

            if attempt >= MAX_RETRIES:
                logger.error(
                    "Tool-call failed after %s retries: %s", MAX_RETRIES, e,
                )
                return None

            delay = _get_retry_delay(e, attempt)
            logger.warning(
                "Temporary tool-call API error (%s). Retrying in %.2fs "
                "(attempt %s/%s)...",
                type(e).__name__, delay, attempt + 1, MAX_RETRIES,
            )
            time.sleep(delay)

    return None