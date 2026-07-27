"""
InsightAI - Executive Report page.
"""
import streamlit as st

from core.theme import apply_theme, confidence_badge_html
from core.setup import setup_resources
from core.report_generator import generate_executive_report

st.set_page_config(page_title="InsightAI - Executive Report", page_icon="📊", layout="wide")
apply_theme()

try:
    workflow_app, _, _ = setup_resources()
except Exception as e:
    st.error("Could not load InsightAI resources.")
    st.exception(e)
    st.stop()

st.title("Executive report")

if "executive_report" not in st.session_state:
    st.session_state.executive_report = None

col_gen, col_spacer = st.columns([1, 4])
with col_gen:
    generate_clicked = st.button("Generate report", type="primary", use_container_width=True)

if generate_clicked:
    with st.spinner("Running analysis across all data sources..."):
        st.session_state.executive_report = generate_executive_report(workflow_app)

report = st.session_state.executive_report

if report is None:
    st.info("Click \"Generate report\" to run a fresh analysis across your sales database, internal documents, and current market context.")
    st.stop()

st.caption(f"Data as of {report['data_as_of']} · Generated {report['generated_at'][:16].replace('T', ' ')} UTC")

st.markdown("##### Executive summary")
st.markdown(report["summary"].replace("$", "\\$"))

st.markdown("##### Key findings")
for f in report["findings"]:
    with st.container(border=True):
        col_q, col_badge = st.columns([4, 1])
        with col_q:
            st.markdown(f"**{f['question']}**")
        with col_badge:
            label = f["confidence"].get("label")
            if label:
                st.markdown(confidence_badge_html(label, f["confidence"].get("score", 0)), unsafe_allow_html=True)

        st.markdown(f["answer"].replace("$", "\\$"))

        if f["conflict_detected"]:
            st.warning(f"⚠️ Conflicting data: {f['conflict_summary'] or 'Sources disagree on this point.'}")

        if f["critique"].get("has_issues"):
            with st.expander(f"Critique: {f['critique'].get('severity', 'unknown')} severity"):
                st.markdown(f["critique"].get("verdict", ""))

st.markdown("##### Recommendations")
st.markdown(report["recommendations"].replace("$", "\\$"))

st.markdown("<br>", unsafe_allow_html=True)

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
)