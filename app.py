
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
from agents.agentic.agent import build_agent_tools, run_agentic_query

from agents.orchestrator.confidence import compute_confidence
from agents.orchestrator.critique import critique_answer
from agents.orchestrator.synthesizer import detect_conflict


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="InsightAI",
    page_icon="📊",
    layout="centered",
)


# ============================================================
# RESOURCE SETUP
# ============================================================

@st.cache_resource(show_spinner="Setting up InsightAI (indexing documents)...")
def setup_resources():
    """
    Initialize all shared InsightAI resources.

    This function runs once per Streamlit session/resource cache.

    Both Workflow and Agent modes share:
    - BM25 index
    - Dense embedding provider
    - Qdrant client
    - Indexed document chunks

    This avoids ingesting and embedding the same documents twice.
    """

    print("\n[Setup] Ingesting documents and building indices...")

    # --------------------------------------------------------
    # 1. Parse documents
    # --------------------------------------------------------

    docs = parse_directory("data/raw")

    if not docs:
        raise RuntimeError(
            "No documents were found in 'data/raw'. "
            "Please add your internal documents before starting InsightAI."
        )


    all_chunks = []

    for document in docs:
        chunks = chunk_document(
            document,
            chunk_size=120,
            chunk_overlap=20,
        )

        all_chunks.extend(chunks)

    if not all_chunks:
        raise RuntimeError(
            "Documents were found, but no chunks were generated."
        )

    texts = [chunk.text for chunk in all_chunks]


    provider = get_provider()

    provider.fit_if_needed(texts)

    dense_vectors = provider.embed_texts(texts)


    bm25 = BM25Index()

    bm25.fit(texts)

    sparse_vectors = [
        bm25.encode(text)
        for text in texts
    ]


    client = get_client()

    ensure_collection(client)

    upsert_chunks(
        client,
        all_chunks,
        dense_vectors,
        sparse_vectors,
    )


    workflow_app = build_orchestrator_graph(
        bm25,
        provider,
        client,
    )


    agent_tools = build_agent_tools(
        bm25,
        provider,
        client,
    )

    print(
        f"[Setup] Indexed {len(all_chunks)} chunks. "
        "Workflow and Agent modes ready."
    )

    return (
        workflow_app,
        agent_tools,
        len(all_chunks),
    )



def extract_agent_results(tool_calls_made: list[dict]):
    """
    Convert Agent mode tool-call history into the same structure
    used by Workflow mode.

    This allows the following components to be shared:

    - Conflict detection
    - Confidence scoring
    - Answer critique

    If a tool is called multiple times, the LAST result is used.
    """

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

    return (
        rag_result,
        sql_result,
        web_result,
    )


# ============================================================
# WORKFLOW MODE EXECUTION
# ============================================================

def run_workflow_query(workflow_app, prompt: str):
    """
    Execute a query using the fixed Workflow architecture.
    """

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

    answer = result.get(
        "final_answer",
        "Sorry, I couldn't generate an answer.",
    )

    meta = {
        "mode": "Workflow (v1)",
        "agents_needed": result.get(
            "agents_needed",
            [],
        ),
        "conflict_detected": result.get(
            "conflict_detected",
            False,
        ),
        "conflict_summary": result.get(
            "conflict_summary",
        ),
        "confidence": result.get(
            "confidence",
        ),
        "critique": result.get(
            "critique",
        ),
        "web_sources": (
            result.get("web_result") or {}
        ).get(
            "sources",
            [],
        ),
    }

    return answer, meta


# ============================================================
# AGENT MODE EXECUTION
# ============================================================

def run_agent_query(prompt: str, agent_tools):
    """
    Execute a query using the Agentic architecture.

    The LLM decides:
    1. Whether tools are needed.
    2. Which tool to call.
    3. What to do with each result.
    4. Whether another tool call is necessary.
    5. When to produce the final answer.
    """

    result = run_agentic_query(
        prompt,
        agent_tools,
    )

    answer = result.get(
        "answer",
        "Sorry, I couldn't generate an answer.",
    )

    tool_calls_made = result.get(
        "tool_calls_made",
        [],
    )

    iterations = result.get(
        "iterations",
        0,
    )


    rag_result = None
    sql_result = None
    web_result = None

    conflict = {
        "conflict_detected": False,
        "conflict_summary": None,
    }

    if iterations == 0:
        # Genuine out-of-scope decline (returned before the loop even started) - High confidence is correct here
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
    """
    Render Markdown while preventing dollar amounts such as
    $92.50 from being interpreted as LaTeX math.
    """

    if not text:
        return

    st.markdown(
        text.replace(
            "$",
            "\\$",
        )
    )


def render_meta(meta: dict):
    """
    Render execution metadata below an assistant response.
    """

    if not meta:
        return

    # --------------------------------------------------------
    # Mode
    # --------------------------------------------------------

    if meta.get("mode"):
        st.caption(
            f"Mode: {meta['mode']}"
        )

    # --------------------------------------------------------
    # Workflow routing
    # --------------------------------------------------------

    agents = meta.get(
        "agents_needed",
        [],
    )

    if agents:
        st.caption(
            f"🔀 Routed to: {', '.join(agents)}"
        )

    # --------------------------------------------------------
    # Agent tool trace
    # --------------------------------------------------------

    tool_trace = meta.get(
        "tool_trace",
        [],
    )

    if tool_trace:

        iterations = meta.get(
            "iterations",
            len(tool_trace),
        )

        with st.expander(
            f"🔁 Agent's actions ({iterations} step(s))"
        ):

            for i, call in enumerate(
                tool_trace,
                1,
            ):

                tool_name = call.get(
                    "tool",
                    "unknown_tool",
                )

                args = call.get(
                    "args",
                    {},
                )

                question = args.get(
                    "question",
                    "",
                )

                st.markdown(
                    f"**Step {i}: `{tool_name}`**"
                )

                if question:
                    st.caption(
                        f"Asked: {question}"
                    )

    # --------------------------------------------------------
    # Conflict detection
    # --------------------------------------------------------

    if meta.get(
        "conflict_detected"
    ):

        st.warning(
            "⚠️ **Conflicting data detected:** "
            + str(
                meta.get(
                    "conflict_summary",
                    "The retrieved sources disagree.",
                )
            )
        )

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    confidence = meta.get(
        "confidence"
    ) or {}

    if confidence.get(
        "label"
    ):

        label = confidence.get(
            "label"
        )

        score = confidence.get(
            "score"
        )

        confidence_icons = {
            "High": "🟢",
            "Medium": "🟡",
            "Low": "🔴",
        }

        icon = confidence_icons.get(
            label,
            "⚪",
        )

        with st.expander(
            f"{icon} Confidence: {label} ({score})"
        ):

            reasons = confidence.get(
                "reasons",
                [],
            )

            for reason in reasons:

                st.markdown(
                    f"- {reason}"
                )

    # --------------------------------------------------------
    # Critique
    # --------------------------------------------------------

    critique = meta.get(
        "critique"
    ) or {}

    if critique.get(
        "has_issues"
    ):

        severity = critique.get(
            "severity",
            "unknown",
        )

        with st.expander(
            f"🔍 Critique flagged: {severity} severity"
        ):

            verdict = critique.get(
                "verdict",
                "",
            )

            if verdict:
                st.markdown(
                    verdict
                )

            findings = critique.get(
                "findings",
                [],
            )

            for finding in findings:

                st.markdown(
                    f"- {finding}"
                )

    # --------------------------------------------------------
    # Web sources
    # --------------------------------------------------------

    web_sources = meta.get(
        "web_sources",
        [],
    )

    if web_sources:

        with st.expander(
            "📚 Web sources"
        ):

            for source in web_sources:

                title = source.get(
                    "title",
                    "Source",
                )

                url = source.get(
                    "url",
                    "#",
                )

                st.markdown(
                    f"- [{title}]({url})"
                )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "### InsightAI"
    )

    st.caption(
        "Multi-Agent Business Analyst Copilot"
    )

    st.divider()

    mode = st.radio(
        "Mode",
        [
            "Workflow (v1)",
            "Agent (v2)",
        ],
        help=(
            "Workflow: a fixed router selects "
            "agents in advance.\n\n"
            "Agent: the LLM dynamically decides "
            "which tools to use and in what order."
        ),
    )

    st.divider()

    st.markdown(
        "**Data sources**"
    )

    st.markdown(
        "- 📄 Internal reports (Doc RAG)\n"
        "- 🗄️ Sales database (SQL)\n"
        "- 🌐 Live web search"
    )

    st.divider()

    st.markdown(
        "**Try asking:**"
    )

    st.caption(
        "What was total revenue by category?"
    )

    st.caption(
        "Who is the current Federal Reserve chair?"
    )

    st.caption(
        "What's driving the 2023 revenue decline?"
    )

    st.divider()

    if st.button(
        "🗑️ Clear chat",
        use_container_width=True,
    ):

        st.session_state.messages = []

        st.rerun()


# ============================================================
# APPLICATION TITLE
# ============================================================

st.title(
    "📊 InsightAI"
)

st.caption(
    f"Mode: **{mode}**"
)


# ============================================================
# INITIALIZE RESOURCES
# ============================================================

try:

    (
        workflow_app,
        agent_tools,
        chunk_count,
    ) = setup_resources()

    st.sidebar.success(
        f"Indexed {chunk_count} document chunks"
    )

except Exception as e:

    st.error(
        "InsightAI failed during startup."
    )

    st.exception(e)

    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# ============================================================
# RENDER CHAT HISTORY
# ============================================================

for msg in st.session_state.messages:

    with st.chat_message(
        msg["role"]
    ):

        safe_markdown(
            msg["content"]
        )

        if (
            msg["role"] == "assistant"
            and msg.get("meta")
        ):

            render_meta(
                msg["meta"]
            )


# ============================================================
# CHAT INPUT
# ============================================================

if prompt := st.chat_input(
    "Ask InsightAI a question..."
):

    # --------------------------------------------------------
    # Save user message
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
            "meta": None,
        }
    )

    with st.chat_message(
        "user"
    ):

        safe_markdown(
            prompt
        )

    # --------------------------------------------------------
    # Generate assistant response
    # --------------------------------------------------------

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "InsightAI is analyzing..."
        ):

            try:

                # ============================================
                # WORKFLOW MODE
                # ============================================

                if mode == "Workflow (v1)":

                    (
                        answer,
                        meta,
                    ) = run_workflow_query(
                        workflow_app,
                        prompt,
                    )

                # ============================================
                # AGENT MODE
                # ============================================

                else:

                    (
                        answer,
                        meta,
                    ) = run_agent_query(
                        prompt,
                        agent_tools,
                    )

            except Exception as e:

                answer = (
                    "I encountered an error while "
                    "processing your question."
                )

                meta = {
                    "mode": mode,
                    "tool_trace": [],
                    "confidence": {
                        "label": "Low",
                        "score": 0.0,
                        "reasons": [
                            "The query could not be completed "
                            "because an internal error occurred."
                        ],
                    },
                    "critique": {
                        "has_issues": True,
                        "severity": "high",
                        "findings": [
                            str(e)
                        ],
                        "verdict": (
                            "The system failed to generate "
                            "a reliable answer."
                        ),
                    },
                }

                st.error(
                    "An internal error occurred."
                )

                with st.expander(
                    "Show technical details"
                ):

                    st.exception(e)

        # ----------------------------------------------------
        # Display answer
        # ----------------------------------------------------

        safe_markdown(
            answer
        )

        # ----------------------------------------------------
        # Display metadata
        # ----------------------------------------------------

        render_meta(
            meta
        )

    # --------------------------------------------------------
    # Save assistant response
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "meta": meta,
        }
    )
