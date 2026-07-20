"""
InsightAI - Shared LLM client wrapper.
Uses generic, provider-agnostic env vars (LLM_API_KEY, LLM_BASE_URL, LLM_MODEL)
per the original design principle: swapping providers is a .env change only.
Falls back to GROQ_-prefixed vars if the generic ones aren't set, for
backward compatibility with any code/.env still using the old names.
"""
import os
import openai
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI

def _get_client():
    api_key = os.getenv("LLM_API_KEY")

    if not api_key:
        return None, None

    base_url = os.getenv(
        "LLM_BASE_URL",
        "https://api.groq.com/openai/v1"
    )

    model = os.getenv(
        "LLM_MODEL",
        "llama-3.1-8b-instant"
    )

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    return client, model


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.0, max_tokens: int | None = None) -> str:
    client, model = _get_client()
    if client is None:
        return ("[No LLM_API_KEY set — skipping generation. "
                 "Add your key to .env to see actual model output.]")

    kwargs = {}
    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        **kwargs,
    )
    return response.choices[0].message.content



def call_llm_with_tools(system_prompt: str, messages: list[dict], tools: list[dict]):
    client, model = _get_client()
    if client is None:
        return None

    try:
        response = client.chat.completions.create(
            model=model, temperature=0,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            tools=tools, tool_choice="auto",
        )
        return response.choices[0].message
    except openai.BadRequestError as e:
        
        print(f"[llm_client] Tool-call generation failed, retrying once: {e}")
        firm_system_prompt = system_prompt + (
            "\n\nIMPORTANT: When calling a tool, output ONLY the structured tool call. "
            "Do not write any reasoning text about which tool to use in the same turn - "
            "decide silently, then call exactly one tool."
        )
        try:
            response = client.chat.completions.create(
                model=model, temperature=0,
                messages=[{"role": "system", "content": firm_system_prompt}] + messages,
                tools=tools, tool_choice="auto",
            )
            return response.choices[0].message
        except openai.BadRequestError as e2:
            print(f"[llm_client] Retry also failed: {e2}")
            return None  # caller must handle this