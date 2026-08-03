"""
InsightAI - Chat page (Workflow v1 / Agent v2). Page config and navigation
are owned centrally by app.py - this file only renders when st.navigation
routes to it.
"""
import html
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
from core.setup import setup_resources
from core.theme2 import apply_theme, severity_icon, section_label

DEBUG_MODE = False

init_db()
apply_theme()


    
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


def run_workflow_query(workflow_app, prompt: str):
    llm_tracker.reset_query()
    initial_state = {
        "query": prompt, "agents_needed": [], "rag_result": None, "sql_result": None,
        "web_result": None, "final_answer": None, "conflict_detected": None,
        "conflict_summary": None, "confidence": None, "critique": None,
    }
    result = workflow_app.invoke(initial_state)
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
        "is_error": False,
    }
    return answer, meta


def run_agent_query(prompt: str, agent_tools):
    result = run_agentic_query(prompt, agent_tools)
    answer = result.get("answer")
    if answer is None or not str(answer).strip():
        answer = "Sorry, I couldn't generate an answer."

    tool_calls_made = result.get("tool_calls_made", [])
    iterations = result.get("iterations", 0)
    rag_result = sql_result = web_result = None
    conflict = {"conflict_detected": False, "conflict_summary": None}

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
        critique = critique_answer(prompt, answer, rag_result, sql_result, web_result)

    meta = {
        "mode": "Agent (v2)", "tool_trace": tool_calls_made, "iterations": iterations,
        "conflict_detected": conflict.get("conflict_detected", False),
        "conflict_summary": conflict.get("conflict_summary"),
        "confidence": confidence, "critique": critique,
        "web_sources": (web_result or {}).get("sources", []),
        "is_error": False,
    }
    return answer, meta


def safe_markdown(text: str):
    if not text:
        return
    st.markdown(text.replace("$", "\\$"))


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
        plain_chips.append(meta["mode"])

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
            for reason in confidence.get("reasons", []):
                st.markdown(f"- {reason}")
        popover_chips.append((f"{icon} {label} · {score}", None, render_confidence))

    critique = meta.get("critique") or {}
    if critique.get("has_issues"):
        severity = critique.get("severity", "unknown")

        def render_critique():
            verdict = critique.get("verdict", "")
            if verdict:
                st.markdown(verdict)
            for finding in critique.get("findings", []):
                st.markdown(f"- {finding}")
        popover_chips.append((f"Critique: {severity}", ":material/search:", render_critique))

    web_sources = meta.get("web_sources", [])
    if web_sources:
        def render_sources():
            for source in web_sources:
                title = source.get("title", "Source")
                url = source.get("url", "#")
                st.markdown(f"- [{title}]({url})")
        popover_chips.append((f"{len(web_sources)} source(s)", ":material/menu_book:", render_sources))

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


def render_assistant_message(answer: str, meta: dict, key: str = "msg"):
    is_error = bool((meta or {}).get("is_error"))
    answer_esc = html.escape(answer or "")

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
                <div style="font-weight:600;color:#B91C1C;margin-bottom:4px;">
                    ⚠ Processing failed
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
        label_visibility="collapsed",
        horizontal=True,
        help=(
            "Workflow: a fixed router selects agents in advance.\n\n"
            "Agent: the LLM dynamically decides which tools to use and in what order."
        ),
    )

    # Data sources
    st.markdown('<div class="ia-section-label">DATA SOURCES</div>', unsafe_allow_html=True)
    with st.popover("3 sources connected", icon=":material/database:", use_container_width=True):
        st.markdown(
            """
            **● Internal reports** — Document RAG  
            **● Sales database** — SQL analytics  
            **● Live web search** — External intelligence
            """
        )

    # History (quick switcher only)
    st.markdown('<div class="ia-section-label">HISTORY</div>', unsafe_allow_html=True)

    conversations = list_conversations(limit=8)
    real_conversations = [
        conv for conv in conversations
        if load_conversation_messages(conv["id"])
    ]

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

            messages = load_conversation_messages(conv["id"])

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

st.title("InsightAI")
st.caption(f"Mode: **{mode}**")

try:
    workflow_app, agent_tools, chunk_count = setup_resources()
    st.sidebar.success(f"Indexed {chunk_count} document chunks")
    st.session_state.chunk_count = chunk_count
except Exception as e:
    st.error("InsightAI failed during startup.")
    if DEBUG_MODE:
        st.exception(e)
    else:
        st.caption("Contact support if this keeps happening.")
    st.stop()

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 28px 20px 18px;
            margin: 12px 0 20px;
        ">
            <div style="font-size:16px;font-weight:600;color:#0F172A;margin-bottom:6px;">
                Ask InsightAI a question
            </div>
            <div style="font-size:13.5px;color:#64748B;max-width:520px;margin:0 auto;line-height:1.5;">
                It will route your question to sales data, internal reports, or the web,
                then show its confidence in the answer.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    example_cols = st.columns(3, gap="medium")
    examples = [
        "What was total revenue by category?",
        "Is the revenue decline mentioned in our reports reflected in the data?",
        "How might current inflation affect future sales?",
    ]
    clicked_example = None
    for col, ex in zip(example_cols, examples):
        with col:
            if st.button(ex, use_container_width=True, key=f"ex_{ex}"):
                clicked_example = ex
else:
    clicked_example = None
    
AVATARS = {"user": ":material/person:", "assistant": ":material/auto_awesome:"}

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar=AVATARS.get(msg["role"])):
        if msg["role"] == "assistant":
            render_assistant_message(msg["content"], msg.get("meta"), key=f"msg_{i}")
        else:
            safe_markdown(msg["content"])

prompt = st.chat_input("Ask InsightAI a question...") or clicked_example

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
        with st.spinner("InsightAI is analyzing..."):
            try:
                if mode == "Workflow (v1)":
                    answer, meta = run_workflow_query(workflow_app, prompt)
                else:
                    answer, meta = run_agent_query(prompt, agent_tools)
            except Exception as e:
                import traceback
                traceback.print_exc()  # surface the real failure on the terminal
                answer = "I encountered an error while processing your question."
                meta = {
                    "mode": mode, "tool_trace": [], "is_error": True,
                    "confidence": {
                        "label": "Low", "score": 0.0,
                        "reasons": ["The query could not be completed because an internal error occurred."],
                    },
                    "critique": {
                        "has_issues": True, "severity": "high",
                        "findings": [f"{type(e).__name__}: {e}", "The query could not be completed because an internal error occurred."],
                        "verdict": "The system failed to generate a reliable answer.",
                    },
                }
                if DEBUG_MODE:
                    with st.expander("Show technical details"):
                        st.exception(e)

        render_assistant_message(answer, meta, key=f"msg_{len(st.session_state.messages)}")
        st.session_state.messages.append({"role": "assistant", "content": answer, "meta": meta})

    save_message(st.session_state.conversation_id, "assistant", answer, meta)

    if len(st.session_state.messages) == 2:
        maybe_set_title_from_first_message(st.session_state.conversation_id, prompt)
    st.rerun()