"""
InsightAI - Environment/secrets resolution.

Single helper for reading configuration secrets so the app works both
locally (dotenv / process env) and on Streamlit Community Cloud
(where secrets are injected via st.secrets). st.secrets is tried first so
deployments can override .env values without changing code; a plain
os.getenv fallback keeps local/local runtimes dependency-free.

All readers are safe outside a running Streamlit session: st.secrets access
is wrapped in try/except and degrades to os.getenv.
"""
import os
from typing import Optional


def read_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Read a secret from st.secrets, falling back to the process environment."""
    try:
        from streamlit import secrets as _st_secrets
        try:
            if key in _st_secrets:
                return str(_st_secrets[key])
        except Exception:
            pass
    except Exception:
        pass

    return os.getenv(key, default)


def read_env_int(key: str, default: int) -> int:
    """Like read_env, but coerces to int."""
    raw = read_env(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default