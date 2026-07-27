"""
InsightAI - Chat page (Workflow v1 / Agent v2). Page config and navigation
are owned centrally by app.py - this file only renders when st.navigation
routes to it.
"""
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
    load_conversation_messages, delete_conversation,
)
from core.llm_client import llm_tracker
from core.setup import setup_resources
from core.theme import apply_theme

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
        "query": prompt,
        "agents_needed": [],
        "rag_result": None,
        "sql_result": None,
        "web_result": None,
        "final_answer": None,
        "conflict_detected": None,
        "conflict_summary": None,
        "confidence": None,
        "critique": None,
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
    }

    return answer, meta


def run_agent_query(prompt: str, agent_tools):
    result = run_agentic_query(prompt, agent_tools)

    answer = result.get("answer")
    if answer is None or not str(answer).strip():
        answer = "Sorry, I couldn't generate an answer."

    tool_calls_made = result.get("tool_calls_made", [])
    iterations = result.get("iterations", 0)

    rag_result = None
    sql_result = None
    web_result = None

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
    }

    return answer, meta


def safe_markdown(text: str):
    if not text:
        return
    st.markdown(text.replace("$", "\\$"))


def render_meta(meta: dict):
    if not meta:
        return

    if meta.get("mode"):
        st.caption(f"Mode: {meta['mode']}")

    agents = meta.get("agents_needed", [])
    if agents:
        st.caption(f"🔀 Routed to: {', '.join(agents)}")

    tool_trace = meta.get("tool_trace", [])
    if tool_trace:
        iterations = meta.get("iterations", len(tool_trace))
        with st.expander(f"🔁 Agent's actions ({iterations} step(s))"):
            for i, call in enumerate(tool_trace, 1):
                tool_name = call.get("tool", "unknown_tool")
                args = call.get("args", {})
                question = args.get("question", "")
                st.markdown(f"**Step {i}: `{tool_name}`**")
                if question:
                    st.caption(f"Asked: {question}")

    if meta.get("conflict_detected"):
        st.warning(
            "⚠️ **Conflicting data detected:** "
            + str(meta.get("conflict_summary", "The retrieved sources disagree."))
        )

    confidence = meta.get("confidence") or {}
    if confidence.get("label"):
        label = confidence.get("label")
        score = confidence.get("score")
        confidence_icons = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
        icon = confidence_icons.get(label, "⚪")
        with st.expander(f"{icon} Confidence: {label} ({score})"):
            for reason in confidence.get("reasons", []):
                st.markdown(f"- {reason}")

    critique = meta.get("critique") or {}
    if critique.get("has_issues"):
        severity = critique.get("severity", "unknown")
        with st.expander(f"🔍 Critique flagged: {severity} severity"):
            verdict = critique.get("verdict", "")
            if verdict:
                st.markdown(verdict)
            for finding in critique.get("findings", []):
                st.markdown(f"- {finding}")

    web_sources = meta.get("web_sources", [])
    if web_sources:
        with st.expander("📚 Web sources"):
            for source in web_sources:
                title = source.get("title", "Source")
                url = source.get("url", "#")
                st.markdown(f"- [{title}]({url})")


with st.sidebar:
    st.markdown("### InsightAI")
    st.caption("Multi-Agent Business Analyst Copilot")
    st.divider()

    mode = st.radio(
        "Mode",
        ["Workflow (v1)", "Agent (v2)"],
        help=(
            "Workflow: a fixed router selects agents in advance.\n\n"
            "Agent: the LLM dynamically decides which tools to use and in what order."
        ),
    )

    st.divider()
    st.markdown("**Data sources**")
    st.markdown(
        "- 📄 Internal reports (Doc RAG)\n"
        "- 🗄️ Sales database (SQL)\n"
        "- 🌐 Live web search"
    )
    st.divider()
    st.markdown("**History**")

    if st.button("New chat", use_container_width=True):
        st.session_state.conversation_id = create_conversation()
        st.session_state.messages = []
        st.rerun()

    conversations = list_conversations()
    for conv in conversations:
        col_open, col_menu = st.columns([5, 1])

        with col_open:
            is_active = conv["id"] == st.session_state.get("conversation_id")
            label = ("● " if is_active else "") + conv["title"]
            if st.button(label, key=f"conv_{conv['id']}", use_container_width=True):
                st.session_state.conversation_id = conv["id"]
                st.session_state.messages = load_conversation_messages(conv["id"])
                st.rerun()

        with col_menu:
            with st.popover("⋮", use_container_width=True):
                confirm_key = f"confirm_del_{conv['id']}"

                if not st.session_state.get(confirm_key):
                    if st.button("Delete conversation", key=f"ask_del_{conv['id']}", use_container_width=True):
                        st.session_state[confirm_key] = True
                        st.rerun()
                else:
                    st.warning("Delete this conversation? This can't be undone.")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Cancel", key=f"cancel_del_{conv['id']}", use_container_width=True):
                            st.session_state[confirm_key] = False
                            st.rerun()
                    with c2:
                        if st.button("Delete", key=f"confirm_del_btn_{conv['id']}", use_container_width=True, type="primary"):
                            delete_conversation(conv["id"])
                            st.session_state.pop(confirm_key, None)
                            if st.session_state.get("conversation_id") == conv["id"]:
                                st.session_state.conversation_id = None
                                st.session_state.messages = []
                            st.rerun()
    st.divider()
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


st.title("InsightAI")
st.caption(f"Mode: **{mode}**")


try:
    workflow_app, agent_tools, chunk_count = setup_resources()
    st.sidebar.success(f"Indexed {chunk_count} document chunks")
    st.session_state.chunk_count = chunk_count
except Exception as e:
    st.error("InsightAI failed during startup.")
    st.exception(e)
    st.stop()


if "conversation_id" not in st.session_state:
    existing = list_conversations(limit=1)
    if existing:
        st.session_state.conversation_id = existing[0]["id"]
        st.session_state.messages = load_conversation_messages(existing[0]["id"])
    else:
        st.session_state.conversation_id = create_conversation()
        st.session_state.messages = []


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        safe_markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("meta"):
            render_meta(msg["meta"])


if prompt := st.chat_input("Ask InsightAI a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt, "meta": None})
    save_message(st.session_state.conversation_id, "user", prompt)

    with st.chat_message("user"):
        safe_markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("InsightAI is analyzing..."):
            try:
                if mode == "Workflow (v1)":
                    answer, meta = run_workflow_query(workflow_app, prompt)
                else:
                    answer, meta = run_agent_query(prompt, agent_tools)
            except Exception as e:
                answer = "I encountered an error while processing your question."
                meta = {
                    "mode": mode, "tool_trace": [],
                    "confidence": {
                        "label": "Low", "score": 0.0,
                        "reasons": ["The query could not be completed because an internal error occurred."],
                    },
                    "critique": {
                        "has_issues": True, "severity": "high",
                        "findings": [str(e)],
                        "verdict": "The system failed to generate a reliable answer.",
                    },
                }
                st.error("An internal error occurred.")
                with st.expander("Show technical details"):
                    st.exception(e)

        safe_markdown(answer)
        render_meta(meta)
        st.session_state.messages.append({"role": "assistant", "content": answer, "meta": meta})

    save_message(st.session_state.conversation_id, "assistant", answer, meta)

    if len(st.session_state.messages) == 2:
        maybe_set_title_from_first_message(st.session_state.conversation_id, prompt)