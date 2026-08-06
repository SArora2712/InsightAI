"""
InsightAI - Dashboard page. Real metrics only: SQL totals, confidence/conflict
stats derived from actual saved conversations, live document chunk count.
"""
import hashlib
import html
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.theme2 import apply_theme, confidence_badge_html, source_tag_html, spacer, INFO, PRIMARY,small_logo_html
from core.history import list_conversations, load_conversation_messages
from agents.sql_agent.executor import execute_sql
from core.setup import setup_resources

st.set_page_config(page_title="InsightAI - Dashboard", page_icon="logo/favicon.png", layout="wide")
apply_theme()


st.markdown(small_logo_html(), unsafe_allow_html=True)

try:
    _, _, chunk_count = setup_resources()
except Exception:
    chunk_count = "—"

st.title("Dashboard")
st.caption("Northwind Traders overview")


def empty_state(message: str):
    """Clean premium empty state – no emojis."""
    st.markdown(
        f"""
        <div style="
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 32px 20px;
            text-align: center;
            color: #64748B;
            font-size: 14px;
            line-height: 1.5;
            margin-top: 6px;
        ">
            {message}
        </div>
        """,
        unsafe_allow_html=True,
    )


# Shared Plotly config (keeps the toolbar clean)
PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "displayModeBar": False,
    "scrollZoom": False,
}

PLOTLY_COLORS = ["#10203D", "#B8935A", "#5A8B8C"]

PLOTLY_LAYOUT_BASE = dict(
    margin=dict(l=10, r=10, t=12, b=10),
    plot_bgcolor="#F7F8FA",
    paper_bgcolor="#F7F8FA",
    font=dict(family="Inter"),
)

AXIS_STYLE = dict(tickfont=dict(size=11, color="#6B7280", family="Inter"))


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


@st.cache_data(ttl=30)
def get_dashboard_stats():
    """Single pass over saved history: feeds avg confidence, conflict count,
    confidence trend, source usage, and query volume without scanning history
    multiple times or re-opening the DB per metric."""
    conversations = list_conversations(limit=50)
    confidence_points = []
    source_counts = {"SQL": 0, "Docs": 0, "Web": 0}
    daily_counts = {}
    scores, conflicts = [], 0
    tag_map = {
        "query_sales_database": "SQL", "sql": "SQL",
        "search_internal_documents": "Docs", "document_rag": "Docs",
        "search_web": "Web", "web": "Web",
    }

    for conv in conversations:
        for msg in load_conversation_messages(conv["id"]):
            if msg.get("role") != "assistant":
                continue
            meta = msg.get("meta") or {}
            created_at = msg.get("created_at")

            confidence = meta.get("confidence") or {}
            score = confidence.get("score")
            if score is not None:
                scores.append(score)
                if created_at:
                    confidence_points.append((created_at, score))

            if meta.get("conflict_detected"):
                conflicts += 1

            sources = set()
            for step in meta.get("tool_trace", []):
                sources.add(step.get("tool", ""))
            for agent in meta.get("agents_needed", []):
                sources.add(agent)
            for s in sources:
                label = tag_map.get(s)
                if label:
                    source_counts[label] += 1

            if created_at:
                day = created_at[:10]
                daily_counts[day] = daily_counts.get(day, 0) + 1

    confidence_points.sort(key=lambda x: x[0])
    avg_confidence = sum(scores) / len(scores) if scores else None
    return {
        "avg_confidence": avg_confidence,
        "conflict_count": conflicts,
        "sample_size": len(scores),
        "confidence_points": confidence_points,
        "source_counts": source_counts,
        "daily_counts": daily_counts,
    }


def confidence_label_from_score(score: float) -> str:
    if score >= 0.7:
        return "High"
    if score >= 0.4:
        return "Medium"
    return "Low"


# ---------------------------------------------------------------------------
# Metrics row
# ---------------------------------------------------------------------------
with st.spinner("Loading dashboard data..."):
    revenue, order_count = get_total_revenue()
    stats = get_dashboard_stats()
    avg_confidence = stats["avg_confidence"]
    conflict_count = stats["conflict_count"]
    sample_size = stats["sample_size"]
    confidence_points = stats["confidence_points"]
    source_counts = stats["source_counts"]
    daily_counts = stats["daily_counts"]

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
    st.metric("Conflicts flagged", str(conflict_count), "This session")
with col4:
    st.metric("Documents indexed", str(chunk_count), "chunks")
spacer("lg")

# ---------------------------------------------------------------------------
# Row 1: revenue by category | confidence trend
# ---------------------------------------------------------------------------
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.markdown("##### Revenue by category")
    try:
        df = get_revenue_by_category()
        if not df.empty:
            fig = go.Figure(go.Bar(
                x=df["revenue"],
                y=df["category"],
                orientation="h",
                marker=dict(color=INFO, line=dict(width=0)),
                text=[f"${v/1_000_000:.1f}M" for v in df["revenue"]],
                textposition="outside",
                textfont=dict(size=12, color="#374151", family="Inter"),
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.0f}<extra></extra>",
            ))
            fig.update_layout(
                height=340,                          # slightly taller for breathing room
                margin=dict(l=8, r=95, t=10, b=10),  # more right margin for labels
                plot_bgcolor="#F7F8FA",
                paper_bgcolor="#F7F8FA",
                showlegend=False,
                xaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(0,0,0,0.04)",
                    showticklabels=False,
                    zeroline=False,
                ),
                yaxis=dict(
                    showgrid=False,
                    autorange="reversed",
                    tickfont=dict(size=12.5, color="#374151", family="Inter"),
                ),
                bargap=0.38,                         # more space between bars
            )
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            empty_state("No category revenue data available yet.")
    except Exception:
        empty_state("Category breakdown isn’t available right now.")

with row1_col2:
    st.markdown("##### Confidence trend")
    if len(confidence_points) >= 2:
        df_conf = pd.DataFrame(confidence_points, columns=["time", "score"])
        df_conf["time"] = pd.to_datetime(df_conf["time"])

        # Simple 3-point moving average for a clean trend line
        df_conf["smooth"] = df_conf["score"].rolling(window=3, min_periods=1, center=True).mean()

        fig2 = go.Figure()

        # Clean trend line only (no raw scatter dots)
        fig2.add_trace(go.Scatter(
            x=df_conf["time"],
            y=df_conf["smooth"],
            mode="lines",
            line=dict(color=INFO, width=2.5),
            hovertemplate="%{x|%b %d, %H:%M}<br>Confidence: %{y:.2f}<extra></extra>",
            name="Trend",
        ))

        fig2.update_layout(
            **PLOTLY_LAYOUT_BASE,
            height=340,
            xaxis=dict(showgrid=False, **AXIS_STYLE),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(0,0,0,0.04)",
                range=[0, 1.08],
                **AXIS_STYLE,
            ),
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        empty_state("Not enough saved queries yet to show a trend.")

spacer("lg")

# ---------------------------------------------------------------------------
# Row 2: source usage | query volume
# ---------------------------------------------------------------------------
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.markdown("##### Source usage")
    if sum(source_counts.values()) > 0:
        fig3 = go.Figure(go.Pie(
            labels=list(source_counts.keys()),
            values=list(source_counts.values()),
            hole=0.62,
            marker=dict(colors=PLOTLY_COLORS),
            textfont=dict(size=12, family="Inter"),
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
        ))
        fig3.update_layout(
            height=340,
            margin=dict(l=10, r=10, t=12, b=10),
            paper_bgcolor="#F7F8FA",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.18,
                font=dict(size=11, family="Inter"),
            ),
        )
        st.plotly_chart(fig3, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        empty_state("No source usage data yet.")

with row2_col2:
    st.markdown("##### Query volume")
    if daily_counts:
        df_daily = pd.DataFrame(sorted(daily_counts.items()), columns=["day", "count"])
        fig4 = go.Figure(go.Bar(
            x=df_daily["day"],
            y=df_daily["count"],
            marker=dict(color=PLOTLY_COLORS[0], line=dict(width=0)),
            hovertemplate="%{x}<br>%{y} queries<extra></extra>",
        ))
        fig4.update_layout(
            **PLOTLY_LAYOUT_BASE,
            height=340,
            xaxis=dict(showgrid=False, **AXIS_STYLE),
            yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.04)", **AXIS_STYLE),
            bargap=0.32,
        )
        st.plotly_chart(fig4, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        empty_state("No query volume data yet.")

spacer("lg")

# ---------------------------------------------------------------------------
# Recent insights (with deduplication)
# ---------------------------------------------------------------------------
st.markdown("##### Recent insights")

conversations = list_conversations(limit=12)  # pull a few more so we can dedupe

if not conversations:
    empty_state("No conversations yet. Head to Chat to ask InsightAI something.")
else:
    shown = 0
    seen_hashes = set()

    for conv in conversations:
        try:
            messages = load_conversation_messages(conv["id"])
            last_assistant_msg = next(
                (m for m in reversed(messages) if m.get("role") == "assistant"), None
            )
            if not last_assistant_msg:
                continue

            meta = last_assistant_msg.get("meta") or {}
            confidence = meta.get("confidence") or {}
            label = confidence.get("label", "Medium")
            score = confidence.get("score", 0.0)

            raw_content = last_assistant_msg.get("content", "")
            title = html.escape(conv.get("title", "Untitled"))

            # Deduplication key: title + first 120 chars of content
            dedupe_key = f"{title}::{raw_content[:120]}".lower().strip()
            content_hash = hashlib.md5(dedupe_key.encode()).hexdigest()

            if content_hash in seen_hashes:
                continue
            seen_hashes.add(content_hash)

            snippet = raw_content[:160].strip() + ("..." if len(raw_content) > 160 else "")
            snippet_escaped = html.escape(snippet).replace("$", "\\$")

            sources = set()
            for step in meta.get("tool_trace", []):
                sources.add(step.get("tool", ""))
            for agent in meta.get("agents_needed", []):
                sources.add(agent)

            tag_map = {
                "query_sales_database": "SQL", "sql": "SQL",
                "search_internal_documents": "Docs", "document_rag": "Docs",
                "search_web": "Web", "web": "Web",
            }
            tags_html = "".join(
                source_tag_html(tag_map.get(s, s)) for s in sources if s
            )

            st.markdown(
                f"""
                <div style="
                    background: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-left: 4px solid {INFO};
                    border-radius: 14px;
                    padding: 16px 18px;
                    margin-bottom: 14px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.03);
                ">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:8px;">
                        <div style="font-weight:600; font-size:14.5px; color:#0F172A; line-height:1.4;">
                            {title}
                        </div>
                        <div>
                            {confidence_badge_html(label, score)}
                        </div>
                    </div>
                    <div style="font-size:13.5px; color:#475569; line-height:1.55; margin-bottom:10px;">
                        {snippet_escaped}
                    </div>
                    <div>{tags_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            shown += 1
            if shown >= 4:          # show up to 4 unique insights
                break

        except Exception as e:
            st.warning(f"Could not load conversation: {e}")

    if shown == 0:
        empty_state("Conversations exist but none have an assistant reply yet.")