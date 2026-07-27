"""
InsightAI - Dashboard page. Real metrics only: SQL totals, confidence/conflict
stats derived from actual saved conversations, live document chunk count.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.theme2 import apply_theme, confidence_badge_html, source_tag_html, spacer, PRIMARY, BORDER, TEXT_SECONDARY
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


@st.cache_data(ttl=60)
def get_revenue_by_category():
    result = execute_sql(
        'SELECT Categories.CategoryName AS category, '
        'SUM("Order Details".UnitPrice * "Order Details".Quantity * (1 - "Order Details".Discount)) AS revenue '
        'FROM "Order Details" '
        'JOIN Products ON "Order Details".ProductID = Products.ProductID '
        'JOIN Categories ON Products.CategoryID = Categories.CategoryID '
        'GROUP BY Categories.CategoryName '
        'ORDER BY revenue DESC'
    )
    return pd.DataFrame(result["rows"])


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


def confidence_label_from_score(score: float) -> str:
    """Mirrors thresholds used elsewhere (agents/orchestrator/confidence.py) -
    verify these match your actual implementation."""
    if score >= 0.7:
        return "High"
    if score >= 0.4:
        return "Medium"
    return "Low"


revenue, order_count = get_total_revenue()
avg_confidence, conflict_count, sample_size = get_confidence_and_conflict_stats()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total revenue", f"${revenue / 1_000_000:.1f}M", f"{order_count:,} orders")
with col2:
    if avg_confidence is not None:
        label = confidence_label_from_score(avg_confidence)
        st.metric("Avg confidence", f"{avg_confidence:.2f}", f"{label}, last {sample_size} queries")
    else:
        st.metric("Avg confidence", "—", "No queries yet")
with col3:
    # Point-in-time counts, not trends - no up-arrow delta (a green arrow
    # here previously implied "improving," which this number doesn't mean).
    st.metric("Conflicts flagged", str(conflict_count))
    st.caption("This session")
with col4:
    st.metric("Documents indexed", str(chunk_count))
    st.caption("chunks")

spacer("lg")

col_chart, col_gap = st.columns([3, 1])
with col_chart:
    st.markdown("##### Revenue by category")
    try:
        df = get_revenue_by_category()
        if not df.empty:
            fig = go.Figure(go.Bar(
                x=df["revenue"],
                y=df["category"],
                orientation="h",
                marker_color=PRIMARY,
                text=[f"${v/1_000_000:.1f}M" for v in df["revenue"]],
                textposition="outside",
                textfont=dict(size=12, color=TEXT_SECONDARY, family="JetBrains Mono"),
            ))
            fig.update_layout(
                height=320,
                margin=dict(l=0, r=40, t=8, b=8),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, visible=False),
                yaxis=dict(showgrid=False, autorange="reversed", tickfont=dict(size=13, family="Inter")),
                showlegend=False,
                bargap=0.35,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No category revenue data available yet.")
    except Exception:
        st.info("Category breakdown isn't available right now.")

spacer("lg")
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
            if tags_html:
                st.markdown(tags_html, unsafe_allow_html=True)