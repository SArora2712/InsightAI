import os
import pytest

KEY_VARS = ("OPENAI_API_KEY",)  # replace with your real variable name(s)


def pytest_collection_modifyitems(config, items):
    if any(os.getenv(k) for k in KEY_VARS):
        return
    skip = pytest.mark.skip(reason="needs an LLM API key (integration test)")
    for item in items:
        if "eval" in item.path.parts:
            item.add_marker(skip)
