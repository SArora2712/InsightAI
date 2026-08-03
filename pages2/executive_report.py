"""
InsightAI - Executive Report page.
"""
import html

import streamlit as st

from core.theme2 import apply_theme, confidence_badge_html, spacer
from core.setup import setup_resources
from core.report_generator import generate_executive_report

st.set_page_config(page_title="InsightAI - Executive Report", page_icon="logo/favicon.png", layout="wide")
apply_theme()

try:
    workflow_app, _, _ = setup_resources()
except Exception as e:
    st.error("Could not load InsightAI resources.")
    st.exception(e)
    st.stop()

st.title("Executive report")
st.caption("Cross-source analysis for leadership")

if "executive_report" not in st.session_state:
    st.session_state.executive_report = None

# Header actions
col_gen, col_info = st.columns([1.2, 4])
with col_gen:
    generate_clicked = st.button(
        "Generate report",
        type="primary",
        use_container_width=True,
        icon=":material/auto_awesome:"
    )

if generate_clicked:
    with st.spinner("Running analysis across all data sources..."):
        st.session_state.executive_report = generate_executive_report(workflow_app)

report = st.session_state.executive_report

if report is None:
    st.info(
        "Click **Generate report** to run a fresh analysis across your sales database, "
        "internal documents, and current market context."
    )
    st.stop()

# Timestamp
st.caption(
    f"Data as of **{report['data_as_of']}** · Generated "
    f"{report['generated_at'][:16].replace('T', ' ')} UTC"
)

spacer("md")

# ===== Executive Summary =====
st.markdown("##### Executive summary")
summary = html.escape(report["summary"] or "").replace("$", r"\$")

st.markdown(
    f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid #E8EAEE;
        border-left: 4px solid #10203D;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 2px 12px rgba(16,32,61,0.06);
        margin-bottom: 8px;
    ">
        <div style="font-size:14.5px; line-height:1.65; color:#1E293B;">
            {summary}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

spacer("lg")

# ===== Key Findings =====
st.markdown("##### Key findings")

for f in report["findings"]:
    label = f["confidence"].get("label")
    score = f["confidence"].get("score", 0)

    st.markdown(
        f"""
        <div style="
            background: #FFFFFF;
            border: 1px solid #E8EAEE;
            border-left: 4px solid #10203D;
            border-radius: 14px;
            padding: 16px 18px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.03);
            margin-bottom: 14px;
        ">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:10px;">
                <div style="font-weight:600; font-size:15px; color:#0F172A; line-height:1.4;">
                    {f["question"]}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Badge + answer (using Streamlit for interactivity)
    col_badge, _ = st.columns([1, 5])
    with col_badge:
        if label:
            st.markdown(confidence_badge_html(label, score), unsafe_allow_html=True)

    answer=f["answer"].replace("$", "\\$")
    st.markdown(answer)

    if f.get("conflict_detected"):
        st.warning(
            f"**Conflicting data:** {f.get('conflict_summary') or 'Sources disagree on this point.'}"
        )

    if f.get("critique", {}).get("has_issues"):
        severity = f["critique"].get("severity", "unknown")
        with st.expander(f"Critique · {severity} severity"):
            st.markdown(f["critique"].get("verdict", "No details available."))

    spacer("sm")

spacer("lg")

# ===== Recommendations =====
st.markdown("##### Recommendations")

# Split recommendations into numbered items if possible
recs = html.escape(report["recommendations"] or "").replace("$", r"\$")

st.markdown(
    f"""
    <div style="
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.03);
    ">
        <div style="font-size:14.5px; line-height:1.7; color:#1E293B;">
            {recs}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

spacer("lg")

# Download
report_markdown = f"""# InsightAI Executive Report

Data as of {report['data_as_of']}

## Executive summary

{report['summary']}

## Key findings

""" + "\n\n".join(
    f"### {f['question']}\n\n{f['answer']}" for f in report["findings"]
) + f"""

## Recommendations

{report['recommendations']}
"""

st.download_button(
    "Download as Markdown",
    data=report_markdown,
    file_name="insightai_executive_report.md",
    mime="text/markdown",
    icon=":material/download:",
)