"""
InsightAI - Dashboard page. Real metrics only: SQL totals, confidence/conflict
stats derived from actual saved conversations, live document chunk count.
"""
import streamlit as st

from core.theme import apply_theme, confidence_badge_html, source_tag_html
from core.history import list_conversations, load_conversation_messages
from agents.sql_agent.executor import execute_sql
from core.setup import setup_resources
st.set_page_config(page_title="InsightAI - Dashboard", page_icon="📊", layout="wide")
apply_theme()
try:
    _, _, chunk_count = setup_resources()
except Exception:
    chunk_count = "—"
st.title("Dashboard")
st.caption("Northwind Traders overview")


@st.cache_data(ttl=60)
def get_total_revenue():
    result = execute_sql(
        'SELECT SUM("Order Details".UnitPrice * "Order Details".Quantity * (1 - "Order Details".Discount)) '
        'AS total_revenue, COUNT(DISTINCT Orders.OrderID) AS order_count '
        'FROM Orders JOIN "Order Details" ON Orders.OrderID = "Order Details".OrderID'
    )
    row = result["rows"][0]
    return row["total_revenue"], row["order_count"]


def get_confidence_and_conflict_stats():
    """Derived from actual saved conversation history, not synthetic data."""
    conversations = list_conversations(limit=20)
    scores, conflicts = [], 0

    for conv in conversations:
        for msg in load_conversation_messages(conv["id"]):
            meta = msg.get("meta")
            if not meta:
                continue
            confidence = meta.get("confidence") or {}
            if confidence.get("score") is not None:
                scores.append(confidence["score"])
            if meta.get("conflict_detected"):
                conflicts += 1

    avg_confidence = sum(scores) / len(scores) if scores else None
    return avg_confidence, conflicts, len(scores)


revenue, order_count = get_total_revenue()
avg_confidence, conflict_count, sample_size = get_confidence_and_conflict_stats()


col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total revenue", f"${revenue / 1_000_000:.1f}M", f"{order_count:,} orders")
with col2:
    if avg_confidence is not None:
        st.metric("Avg confidence", f"{avg_confidence:.2f}", f"High, last {sample_size} queries")
    else:
        st.metric("Avg confidence", "—", "No queries yet")
with col3:
    st.metric("Conflicts flagged", str(conflict_count), "This session")
with col4:
    st.metric("Documents indexed", str(chunk_count), "chunks")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("##### Recent insights")

conversations = list_conversations(limit=3)
if not conversations:
    st.info("No conversations yet. Head to Chat to ask InsightAI something.")
else:
    for conv in conversations:
        messages = load_conversation_messages(conv["id"])
        last_assistant_msg = next((m for m in reversed(messages) if m["role"] == "assistant"), None)
        if not last_assistant_msg:
            continue

        meta = last_assistant_msg.get("meta") or {}
        confidence = meta.get("confidence") or {}
        label = confidence.get("label", "Medium")

        with st.container(border=True):
            col_title, col_badge = st.columns([4, 1])
            with col_title:
              st.markdown(f"**{conv['title'].replace('$', chr(92) + '$')}**")  
            with col_badge:
                st.markdown(confidence_badge_html(label, confidence.get("score", 0)), unsafe_allow_html=True)

            raw_content = last_assistant_msg["content"]
            snippet = raw_content[:180]
            if len(raw_content) > 180:
                snippet += "..."
            st.caption(snippet.replace("$", "\\$"))
            

            tags_html = ""
            if meta.get("tool_trace") or meta.get("agents_needed"):
                sources = set()
                for step in meta.get("tool_trace", []):
                    sources.add(step.get("tool", ""))
                for agent in meta.get("agents_needed", []):
                    sources.add(agent)
                tag_map = {"query_sales_database": "SQL", "sql": "SQL",
                           "search_internal_documents": "Docs", "document_rag": "Docs",
                           "search_web": "Web", "web": "Web"}
                for s in sources:
                    tags_html += source_tag_html(tag_map.get(s, s))
            st.markdown(tags_html, unsafe_allow_html=True)