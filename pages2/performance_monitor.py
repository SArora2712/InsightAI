"""
InsightAI - Performance Monitor page (admin only).

Operational readout of the LLM call budget and token usage tracked by
core.llm_client's LLMCallTracker, plus index/resource status. This page is
gated behind the app's admin role (see core.auth) and kept intentionally
light - it reads in-process counters, not a metrics backend.
"""
import streamlit as st

from core.theme2 import apply_theme, spacer, INFO, DANGER, stat_card, small_logo_html
from core.auth import is_admin
from core.llm_client import llm_tracker, _effective_limit
from core.setup import setup_resources
from core.history import list_conversations


st.set_page_config(page_title="InsightAI · Performance", page_icon="logo/favicon.svg", layout="wide")
apply_theme()
st.markdown(small_logo_html(), unsafe_allow_html=True)

if not is_admin():
    st.title("Performance monitor")
    st.info(
        "Admin access required. Sign in with an admin account to view "
        "performance monitoring."
    )
    st.stop()

try:
    _, _, chunk_count = setup_resources()
except Exception:
    chunk_count = "—"

st.title("Performance monitor")
st.caption("LLM call budget, token usage, and resource status")

usage = llm_tracker.snapshot()
limit = _effective_limit()
# `pct` and the "X of Y" caption must reference the SAME metric: the current
# query's LLM call count against the per-query call budget. (Previously the
# caption showed the session call total against that same per-query limit,
# e.g. "38 of 15", which mixes two different units.)
query_calls = usage["query_count"]
headroom = max(0, limit - query_calls)
pct = round(100 * query_calls / limit, 1) if limit else 0.0
budget_accent = INFO if pct < 70 else (DANGER if pct >= 90 else "#D97706")

col1, col2, col3, col4 = st.columns(4)
with col1:
    stat_card(
        "LLM calls (this query)", str(query_calls),
        f"budget {limit} · headroom {headroom}", INFO,
    )
with col2:
    stat_card(
        "Tokens (this query)", f"{usage['query_tokens']:,}",
        f"session {usage['session_tokens']:,}", INFO,
    )
with col3:
    stat_card(
        "LLM calls (session)", str(usage["session_total"]),
        "this session", "#94A3B8",
    )
with col4:
    stat_card(
        "Call budget used", f"{pct:.0f}%",
        f"{query_calls} of {limit} calls", budget_accent,
    )

spacer("lg")

# ---- Resource status ----
st.markdown("##### Resource status")
res_col1, res_col2 = st.columns(2)
with res_col1:
    stat_card("Documents indexed", str(chunk_count), "chunks", "#94A3B8")
with res_col2:
    try:
        conv_count = len(list_conversations(limit=1000))
    except Exception:
        conv_count = "—"
    stat_card("Conversations", str(conv_count), "saved in SQLite", INFO)