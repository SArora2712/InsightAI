"""
InsightAI - Executive Report page.
"""
import html

import streamlit as st

from core.theme2 import apply_theme, confidence_badge_html, spacer, small_logo_html
from core.setup import setup_resources
from core.progress import StepTracker
from core.report_generator import (
    generate_executive_report,
    EXECUTIVE_REPORT_STEPS,
)
from core.text_utils import strip_inline_code, clean_prose

st.set_page_config(page_title="InsightAI · Executive Report", page_icon="logo/favicon.svg", layout="wide")
apply_theme()
st.markdown(small_logo_html(), unsafe_allow_html=True)

try:
    workflow_app, _, _ = setup_resources()
except Exception as e:
    st.error("Could not load InsightAI resources.")
    st.exception(e)
    st.stop()

st.title("Executive report")
st.caption("Cross-source analysis for leadership")

st.markdown(
    "Generates a leadership brief from three sources — your sales database, "
    "internal business reports, and current market context. InsightAI answers "
    "a fixed set of strategic questions, then compiles an executive summary, "
    "key findings with confidence scores, and recommendations."
)

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
with col_info:
    regen_hint = st.session_state.executive_report is not None
    st.markdown(
        (
            'Last generated: <b>not yet</b> — click Generate report to create '
            "your first brief."
            if not regen_hint
            else f"Click Generate report again to refresh this brief."
        ),
        unsafe_allow_html=True,
    )

if generate_clicked:
    with st.status("Running the report pipeline…", expanded=False) as status:
        status.update(label="Running the report pipeline…", state="running")
        tracker = StepTracker(steps=EXECUTIVE_REPORT_STEPS)

        def progress(step_label):
            tracker.advance(step_label)
            status.update(label=f"{tracker.active}…", state="running")

        try:
            st.session_state.executive_report = generate_executive_report(
                workflow_app, progress=progress
            )
        except Exception as exc:
            st.session_state.executive_report = None
            tracker.complete()
            st.error(f"Report generation failed: {exc}")
            status.update(label="Report generation failed", state="error")
        else:
            tracker.complete()
            status.update(label="Report complete", state="complete")

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
summary = html.escape(strip_inline_code(report["summary"] or ""))

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
    question = f["question"]

    with st.container(border=True):
        head_l, head_r = st.columns(
            [4.45, 1], gap="small", vertical_alignment="center"
        )
        with head_l:
            st.markdown(f"**{question}**")
        with head_r:
            if label:
                st.markdown(confidence_badge_html(label, score), unsafe_allow_html=True)

        st.markdown(clean_prose(f["answer"]))

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
recs = html.escape(strip_inline_code(report["recommendations"] or ""))

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