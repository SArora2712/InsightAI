"""
InsightAI - Chat page (Workflow v1 / Agent v2). Page config and navigation
are owned centrally by app.py - this file only renders when st.navigation
routes to it.
"""
import html
import time
import streamlit as st

from ingestion.parser import parse_directory
from ingestion.chunker import chunk_document
from ingestion.vector_store import (
    get_client,
    ensure_collection,
    upsert_chunks,
)
from ingestion.sparse import BM25Index
from ingestion.embeddings import get_provider

from agents.orchestrator.graph import build_orchestrator_graph
from agents.agentic.agent import build_agent_tools
from agents.agentic.graph_loop import run_agentic_query_v2 as run_agentic_query

from agents.orchestrator.confidence import compute_confidence
from agents.orchestrator.critique import critique_answer
from agents.orchestrator.synthesizer import detect_conflict
from core.history import (
    init_db, create_conversation, save_message,
    maybe_set_title_from_first_message, list_conversations,
    load_conversation_messages, delete_conversation,rename_conversation
)
from core.llm_client import llm_tracker
from core.logging_util import get_logger
from core.setup import setup_resources
from core.progress import StepTracker, PROCESSING_STEPS
from core.text_utils import clean_prose
from core.theme2 import apply_theme, severity_icon, section_label, favicon_mark_svg, CONFIDENCE_LEGEND

DEBUG_MODE = False

logger = get_logger("page.chat2")

init_db()
apply_theme()


@st.cache_data(ttl=10, show_spinner=False)
def get_recent_conversations(limit: int = 8, max_updated_at: str = "") -> list[dict]:
    """
    Load the N most recent conversations together with their messages in a
    single pass. `max_updated_at` is the max conversations.updated_at from the
    previous rerun — a new/moved conversation bumps it, invalidating the cache
    instead of re-querying on every rerun (fixes the old N+1 in the sidebar).
    """
    conversations = list_conversations(limit=limit)
    results = []
    for conv in conversations:
        messages = load_conversation_messages(conv["id"])
        if not messages:
            continue
        results.append({"id": conv["id"], "title": conv["title"], "messages": messages})
    return results


    
def extract_agent_results(tool_calls_made: list[dict]):
    rag_result = None
    sql_result = None
    web_result = None
    for call in tool_calls_made or []:
        tool_name = call.get("tool")
        tool_result = call.get("result")
        if tool_name == "query_sales_database":
            sql_result = tool_result
        elif tool_name == "search_web":
            web_result = tool_result
        elif tool_name == "search_internal_documents":
            rag_result = tool_result
    return rag_result, sql_result, web_result


_TOOL_STEP = {
    "query_sales_database": "Run SQL query",
    "search_internal_documents": "Search documents",
}


def _progress_wrapped_tools(agent_tools, progress):
    wrapped = {}
    for name, fn in (agent_tools or {}).items():
        step = _TOOL_STEP.get(name)
        if step is None:
            wrapped[name] = fn
            continue

        def make(fn=fn, step=step):
            def call(*args, **kwargs):
                progress(step)
                return fn(*args, **kwargs)
            return call

        wrapped[name] = make()
    return wrapped


def run_workflow_query(workflow_app, prompt: str, progress=None):
    llm_tracker.reset_query()
    initial_state = {
        "query": prompt, "agents_needed": [], "rag_result": None, "sql_result": None,
        "web_result": None, "final_answer": None, "conflict_detected": None,
        "conflict_summary": None, "confidence": None, "critique": None,
    }

    node_step_map = {
        "sql_agent": "Run SQL query",
        "rag_agent": "Search documents",
        "synthesize": "Synthesize answer",
        "confidence_critique": "Review answer",
    }

    if progress is None:
        result = workflow_app.invoke(initial_state)
    else:
        # stream_mode="updates" yields one event per completed node, so the
        # UI can advance the sequential step indicator as nodes finish.
        result = dict(initial_state)
        for event in workflow_app.stream(initial_state, stream_mode="updates"):
            for node_name, payload in event.items():
                step = node_step_map.get(node_name)
                if step:
                    progress(step)
                if isinstance(payload, dict):
                    result.update(payload)

    answer = result.get("final_answer")
    if answer is None or not str(answer).strip():
        answer = "Sorry, I couldn't generate an answer."
    meta = {
        "mode": "Workflow (v1)",
        "agents_needed": result.get("agents_needed", []),
        "conflict_detected": result.get("conflict_detected", False),
        "conflict_summary": result.get("conflict_summary"),
        "confidence": result.get("confidence"),
        "critique": result.get("critique"),
        "web_sources": (result.get("web_result") or {}).get("sources", []),
        "llm_usage": llm_tracker.snapshot(),
        "is_error": False,
    }
    return answer, meta


def run_agent_query(prompt: str, agent_tools, progress=None):
    if progress is not None:
        agent_tools = _progress_wrapped_tools(agent_tools, progress)
    result = run_agentic_query(prompt, agent_tools)
    answer = result.get("answer")
    if answer is None or not str(answer).strip():
        answer = "Sorry, I couldn't generate an answer."

    tool_calls_made = result.get("tool_calls_made", [])
    iterations = result.get("iterations", 0)
    rag_result = sql_result = web_result = None
    conflict = {"conflict_detected": False, "conflict_summary": None}

    if progress is not None:
        progress("Synthesize answer")

    if iterations == 0:
        confidence = {"score": 1.0, "label": "High", "reasons": ["Correctly declined — out of scope."]}
        critique = {"has_issues": False, "severity": "none", "findings": [], "verdict": "N/A — out of scope"}
    elif not tool_calls_made:
        confidence = {"score": 0.1, "label": "Low", "reasons": ["No tool was called despite the question being in-scope — answer is not grounded in any source."]}
        critique = {"has_issues": True, "severity": "severe", "findings": ["No tool results back this answer."], "verdict": "Answer is ungrounded."}
    else:
        rag_result, sql_result, web_result = extract_agent_results(tool_calls_made)
        conflict = detect_conflict(rag_result, sql_result, web_result)
        confidence = compute_confidence(conflict["conflict_detected"], rag_result, sql_result, web_result)
        if progress is not None:
            progress("Review answer")
        critique = critique_answer(prompt, answer, rag_result, sql_result, web_result)

    meta = {
        "mode": "Agent (v2)", "tool_trace": tool_calls_made, "iterations": iterations,
        "conflict_detected": conflict.get("conflict_detected", False),
        "conflict_summary": conflict.get("conflict_summary"),
        "confidence": confidence, "critique": critique,
        "web_sources": (web_result or {}).get("sources", []),
        "llm_usage": llm_tracker.snapshot(),
        "is_error": False,
    }
    return answer, meta


def safe_markdown(text: str):
    if not text:
        return
    st.markdown(text)


def render_chip_row(meta: dict, key: str = "chip"):
    """Single horizontal row of compact chips. Plain-text spans for
    non-interactive chips; real st.popover(icon=...) for interactive ones -
    icon= is a dedicated Streamlit parameter that reliably renders Material
    icons, unlike typing ':material/name:' inline inside label text, which
    is not parsed in popover/markdown labels on this version and shows as
    literal text instead."""
    if not meta:
        return

    plain_chips = []      # label only, rendered as a styled span
    popover_chips = []     # (label, icon, render_fn)

    if meta.get("mode"):
        plain_chips.append(meta["mode"].replace(" (v1)", "").replace(" (v2)", ""))

    agents = meta.get("agents_needed", [])
    if agents:
        plain_chips.append(", ".join(agents))

    tool_trace = meta.get("tool_trace", [])
    if tool_trace:
        iterations = meta.get("iterations", len(tool_trace))

        def render_trace():
            for i, call in enumerate(tool_trace, 1):
                tool_name = call.get("tool", "unknown_tool")
                args = call.get("args", {})
                question = args.get("question", "")
                st.markdown(f"**Step {i}: `{tool_name}`**")
                if question:
                    st.caption(f"Asked: {question}")
        popover_chips.append((f"{iterations} step(s)", ":material/sync:", render_trace))

    confidence = meta.get("confidence") or {}
    if confidence.get("label"):
        label = confidence.get("label")
        score = confidence.get("score")
        icon = severity_icon(label)

        def render_confidence():
            st.markdown(f"*Confidence scale: {CONFIDENCE_LEGEND}*")
            for reason in confidence.get("reasons", []):
                st.markdown(f"- {reason}")
        popover_chips.append((f"{icon} {label} · {score}", None, render_confidence))

    critique = meta.get("critique") or {}
    if critique.get("has_issues"):
        severity = critique.get("severity", "unknown")

        def render_critique():
            st.markdown(
                "_An internal review step that checks the answer against "
                "source data before it is returned to you._"
            )
            verdict = critique.get("verdict", "")
            if verdict:
                st.markdown(verdict)
            for finding in critique.get("findings", []):
                st.markdown(f"- {finding}")
        popover_chips.append((f"Critique: {severity} ⓘ", ":material/search:", render_critique))

    web_sources = meta.get("web_sources", [])
    if web_sources:
        def render_sources():
            for source in web_sources:
                title = source.get("title", "Source")
                url = source.get("url", "#")
                st.markdown(f"- [{title}]({url})")
        popover_chips.append((f"{len(web_sources)} source(s)", ":material/menu_book:", render_sources))

    llm_usage = meta.get("llm_usage")
    if llm_usage and llm_usage.get("query_count"):
        calls = llm_usage.get("query_count", 0)
        tokens = llm_usage.get("query_tokens", 0)

        def render_usage():
            st.markdown(
                f"**{calls} LLM call(s)** · {tokens:,} tokens "
                f"(session total: {llm_usage.get('session_total', 0)} calls, "
                f"{llm_usage.get('session_tokens', 0):,} tokens)"
            )
        popover_chips.append((f"{calls} LLM call(s)", ":material/search:", render_usage))

    total_chips = len(plain_chips) + len(popover_chips)
    if total_chips == 0:
        return

    with st.container(key=f"chip_row_{key}"):
        cols = st.columns(total_chips)
        col_idx = 0

        for label in plain_chips:
            with cols[col_idx]:
                st.markdown(
                    f'''
                    <span style="
                        font-size:12px;
                        font-weight:500;
                        color:#64748B;
                        background:#F1F5F9;
                        border-radius:999px;
                        padding:4px 11px;
                        display:inline-block;
                        margin-right:6px;
                    ">{label}</span>
                    ''',
                    unsafe_allow_html=True,
                )
            col_idx += 1

        for label, icon, render_fn in popover_chips:
            with cols[col_idx]:
                with st.popover(label, icon=icon):
                    render_fn()
            col_idx += 1

    if meta.get("conflict_detected"):
        st.warning(
            "**Conflicting data detected:** "
            + str(meta.get("conflict_summary", "The retrieved sources disagree."))
        )


def render_assistant_message(answer: str, meta: dict, key: str = "msg", processing_steps=None):
    """Render a saved assistant message: a single clean "Analysis complete"
    line when the message was produced by a live run (no itemized step
    breakdown), the answer card, and the metadata chip row. `processing_steps`
    only flags that a run happened — the breakdown itself is no longer shown."""
    if processing_steps:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:6px;font-size:13px;'
            'font-weight:600;color:#0F766E;margin:1px 2px 6px;cursor:default;">'
            '<span style="color:#14B8A6;font-size:14px;">✓</span>'
            "Analysis complete</div>",
            unsafe_allow_html=True,
        )
    is_error = bool((meta or {}).get("is_error"))
    answer_esc = html.escape(clean_prose(answer or ""))

    if is_error:
        st.markdown(
            f"""
            <div style="
                background:#FEF2F2;
                border:1px solid #FECACA;
                border-left:4px solid #EF4444;
                border-radius:14px;
                padding:16px 18px;
                margin-bottom:8px;
            ">
                <div style="font-weight:600;color:#B91C1C;margin-bottom:4px;display:flex;align-items:center;gap:6px;">
                    <span class="material-symbols-rounded" style="font-size:17px;">error</span>
                    Processing failed
                </div>
                <div style="color:#7F1D1D;">{answer_esc}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style="
                background:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:14px;
                padding:16px 18px;
                box-shadow:0 2px 12px rgba(0,0,0,0.04);
                margin-bottom:6px;
            ">
                <div style="font-size:14.5px;line-height:1.65;color:#1E293B;">
                    {answer_esc}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    render_chip_row(meta, key=f"chip_{key}")

with st.sidebar:

    # New analysis
    if st.button(
        "New analysis",
        use_container_width=True,
        icon=":material/add:",
        type="primary",
        key="new_analysis_btn",
    ):
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.rerun()

    # AI Mode
    st.markdown('<div class="ia-section-label">AI MODE</div>', unsafe_allow_html=True)
    mode = st.radio(
        "Mode",
        ["Workflow (v1)", "Agent (v2)"],
        format_func=lambda x: x.replace(" (v1)", "").replace(" (v2)", ""),
        label_visibility="collapsed",
        horizontal=True,
        help=(
            "Workflow: a fixed router selects agents in advance.\n\n"
            "Agent: the LLM dynamically decides which tools to use and in what order."
        ),
    )

    # Data sources
    st.markdown('<div class="ia-section-label">DATA SOURCES</div>', unsafe_allow_html=True)
    with st.popover("Sales DB · Reports · Documents", icon=":material/database:", key="src_pop", use_container_width=True):
        st.caption("3 sources connected")
        st.markdown(
            """
            **● Internal reports** — Document RAG  
            **● Sales database** — SQL analytics  
            **● Live web search** — External intelligence
            """
        )

    # Recent conversations (quick switcher only)
    st.markdown('<div class="ia-section-label">RECENT</div>', unsafe_allow_html=True)

    try:
        _recent_meta = list_conversations(limit=8)
        max_updated_at = max(
            (c.get("updated_at") or "" for c in _recent_meta),
            default="",
        )
        real_conversations = get_recent_conversations(limit=8, max_updated_at=max_updated_at)
    except Exception:
        real_conversations = []

    if not real_conversations:
        st.markdown(
            """
            <div class="ia-history-empty">
                <div class="ia-empty-title">No analyses yet</div>
                <div class="ia-empty-text">Start a new analysis to see it here.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for conv in real_conversations:
            is_active = conv["id"] == st.session_state.get("conversation_id")
            row_key = f"history_row_active_{conv['id']}" if is_active else f"history_row_{conv['id']}"
            
            title = (conv.get("title") or "Untitled").strip()
            if len(title) > 34:
                title = title[:34] + "…"

            messages = conv.get("messages") or []

            with st.container(key=row_key):
                if st.button(title, key=f"conv_{conv['id']}", use_container_width=True):
                    st.session_state.conversation_id = conv["id"]
                    st.session_state.messages = messages
                    st.rerun()
    st.divider()

    if st.button("Clear chat", use_container_width=True, icon=":material/delete_sweep:"):
        st.session_state.messages = []
        st.rerun()
    if st.button(
        "Settings",
        use_container_width=True,
        icon=":material/settings:",
    ):
        st.info("Settings will be available soon.")

    if st.button(
        "Help & feedback",
        use_container_width=True,
        icon=":material/help_outline:",
    ):
        st.info("Help center will be available soon.")

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

if len(st.session_state.messages) == 0:
    hero_html = (
        "<div class='ia-hero'>"
        "<div class='ia-logo'>" + favicon_mark_svg() + "</div>"
        "<div class='ia-hero-name'>Insight<span>AI</span></div>"
        "<div class='ia-hero-sub'>What would you like to analyze?</div>"
        "</div>"
    )
else:
    hero_html = (
        "<div class='ia-hero ia-hero--compact'>"
        "<div class='ia-logo'>" + favicon_mark_svg() + "</div>"
        "<div class='ia-hero-name'>Insight<span>AI</span></div>"
        "</div>"
    )

st.markdown(hero_html, unsafe_allow_html=True)
try:
    workflow_app, agent_tools, chunk_count = setup_resources()
    st.session_state.chunk_count = chunk_count
except Exception as e:
    st.error("InsightAI could not connect to its data index.")
    st.write(
        "This usually happens when another InsightAI instance is already "
        "running — the embedded index allows only one at a time. Close the "
        "other instance and retry, or set `QDRANT_URL` / `QDRANT_API_KEY` "
        "for shared access."
    )
    if DEBUG_MODE:
        with st.expander("Show technical details"):
            st.exception(e)
    if st.button("Retry connection", icon=":material/refresh:", type="primary"):
        setup_resources.clear()
        st.rerun()
    st.stop()

if not st.session_state.messages:
    st.markdown(
        '<div class="ia-suggestion-label">Suggested analyses</div>',
        unsafe_allow_html=True,
    )
    example_cols = st.columns(3, gap="medium")
    examples = [
        ("Revenue performance", "What was total revenue by category?", ":material/bar_chart:"),
        ("Business trends", "Is the revenue decline mentioned in our reports reflected in the data?", ":material/trending_up:"),
        ("Forecasting", "How might current inflation affect future sales?", ":material/query_stats:"),
    ]
    clicked_example = None
    for col, (title, question, icon) in zip(example_cols, examples):
        with col:
            if st.button(
                f"{title}\n{question}",
                key=f"sugg_{title}",
                use_container_width=True,
                icon=icon,
            ):
                clicked_example = question
else:
    clicked_example = None
    
AVATARS = {"user": ":material/person:", "assistant": ":material/auto_awesome:"}

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar=AVATARS.get(msg["role"])):
        if msg["role"] == "assistant":
            render_assistant_message(
                msg["content"],
                msg.get("meta"),
                key=f"msg_{i}",
                processing_steps=msg.get("processing_steps"),
            )
        else:
            safe_markdown(msg["content"])

prompt = st.chat_input("Ask InsightAI about your business...") or clicked_example

if prompt:
    if st.session_state.conversation_id is None:
        st.session_state.conversation_id = create_conversation()
        st.session_state.messages = []
    last_msg = st.session_state.messages[-1] if st.session_state.messages else None
    if not last_msg or last_msg["content"] != prompt or last_msg["role"] != "user":
        st.session_state.messages.append({"role": "user", "content": prompt, "meta": None})
        save_message(st.session_state.conversation_id, "user", prompt)
    with st.chat_message("user", avatar=AVATARS["user"]):
        safe_markdown(prompt)

    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        with st.status("Analyzing your question…", expanded=False) as status:
            status.update(label="Analyzing your question…", state="running")
            tracker = StepTracker()

            # Single-line progress: the status label itself is the indicator, and
            # it updates to the newly-active step as each one begins. Pacing keeps
            # every label visible for a moment (Streamlit streams deltas to the
            # browser while the script runs) instead of flashing through instantly.
            MIN_STEP_SECONDS = 0.45
            _last_step_at = [0.0]

            def progress(step_label):
                remaining = MIN_STEP_SECONDS - (time.monotonic() - _last_step_at[0])
                if remaining > 0 and tracker.active is not None:
                    time.sleep(remaining)
                tracker.advance(step_label)
                _last_step_at[0] = time.monotonic()
                status.update(label=f"{tracker.active}…", state="running")

            try:
                if mode == "Workflow (v1)":
                    answer, meta = run_workflow_query(workflow_app, prompt, progress=progress)
                else:
                    answer, meta = run_agent_query(prompt, agent_tools, progress=progress)
            except Exception as e:
                logger.error("Chat query failed: %s", e, exc_info=True)
                answer = "I encountered an error while processing your question."
                meta = {
                    "mode": mode, "tool_trace": [], "is_error": True,
                    "confidence": {
                        "label": "Low", "score": 0.0,
                        "reasons": ["The query could not be completed because an internal error occurred."],
                    },
                    "critique": {
                        "has_issues": True, "severity": "high",
                        "findings": ["The query could not be completed because an internal error occurred."],
                        "verdict": "The system failed to generate a reliable answer.",
                    },
                }
                tracker.complete()
                if DEBUG_MODE:
                    with st.expander("Show technical details"):
                        st.exception(e)
                status.update(label="Analysis failed", state="error")
            else:
                tracker.complete()
                status.update(label="Analysis complete", state="complete")

        render_assistant_message(answer, meta, key=f"msg_{len(st.session_state.messages)}")
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "meta": meta,
                "processing_steps": list(PROCESSING_STEPS),
            }
        )

    save_message(st.session_state.conversation_id, "assistant", answer, meta)

    if len(st.session_state.messages) == 2:
        maybe_set_title_from_first_message(st.session_state.conversation_id, prompt)
    st.rerun()