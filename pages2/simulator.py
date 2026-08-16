"""
InsightAI - What-If Decision Simulator page.
Wraps agents.simulator.run_decision_simulator (adjust the import path below
to wherever this file actually lives in your project).
"""
import streamlit as st
from datetime import datetime

from core.theme2 import apply_theme, banner_html, spacer, small_logo_html
from core.formatting import format_currency
from core.text_utils import clean_prose

# Adjust this import to the actual module path for run_decision_simulator
from agents.simulator.decision_simulator import run_decision_simulator

st.set_page_config(page_title="InsightAI · Simulator", page_icon="logo/favicon.svg", layout="wide")
apply_theme()
st.markdown(small_logo_html(), unsafe_allow_html=True)

SIM_CSS = """<style>
/* Section header for the Analysis block - matches other in-app headers
   (e.g. "Recent insights") with a subtle top divider for hierarchy. */
.sim-section-header {
    font-size: 16px;
    font-weight: 700;
    color: #10203D;
    margin: 0 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #E4E7EC;
    letter-spacing: -0.01em;
}
</style>"""
st.markdown(SIM_CSS, unsafe_allow_html=True)

st.title("Simulator")
st.caption("What-if projections from real current data — no elasticity modeled")

st.markdown(
    "Describe a business change, like “What if we increase Beverages price by "
    "10%?”. InsightAI computes a straight-line projection from current sales "
    "data, showing the estimated impact on revenue and unit economics while "
    "holding everything else constant."
)

if "simulator_history" not in st.session_state:
    st.session_state.simulator_history = []

question = st.text_input(
    "Scenario",
    placeholder="What if we increase Beverages price by 10%?",
    label_visibility="collapsed",
)
run_clicked = st.button(
    "Run simulation",
    type="primary",
    disabled=not question.strip(),
)

if run_clicked and question.strip():
    with st.status("Computing projection…", expanded=False) as status:
        status.update(label="Running what-if projection", state="running")
        result = run_decision_simulator(question)
        if result.get("error"):
            status.update(label="Projection failed", state="error")
        else:
            status.update(label="Projection complete", state="complete")
        st.session_state["simulator_last_run"] = datetime.now().strftime(
            "%b %d, %Y · %H:%M"
        )
    st.session_state.simulator_history.insert(0, result)

if st.session_state.get("simulator_last_run"):
    st.caption(f"Last run: {st.session_state['simulator_last_run']}")

if st.session_state.simulator_history:
    latest = st.session_state.simulator_history[0]

    if latest["error"]:
        st.warning(latest["error"])
    else:
        scenario = latest["scenario"]
        computed = latest["computed"]

        st.markdown(
            f"**Scenario:** {scenario['metric']} for **{scenario['target']}** "
            f"changed by **{scenario['change_percent']:+.1f}%**"
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current revenue", format_currency(computed["current_revenue"], style="full"))
        with col2:
            st.metric(
                "Projected revenue",
                format_currency(computed["projected_revenue"], style="full"),
                f"{computed['revenue_delta_pct']:+.1f}%",
            )
        with col3:
            st.metric("Current avg. unit price", format_currency(computed["current_avg_price"], style="full", decimals=2))

        with st.container(border=True):
            st.markdown(
                '<div class="sim-section-header">Analysis</div>',
                unsafe_allow_html=True,
            )
            st.markdown(clean_prose(latest["answer"] or ""))

        # Previously an inline-styled <div> with hardcoded hex colors that
        # duplicated (and could drift from) theme.py's AMBER tokens. Now
        # goes through the same helper used for conflict/error banners
        # elsewhere in the app.
        st.markdown(
            banner_html(
                "This is a straight-line projection holding all else constant — it does not model "
                "price elasticity, customer behavior change, or competitive response.",
                kind="warning",
            ),
            unsafe_allow_html=True,
        )

if len(st.session_state.simulator_history) > 1:
    spacer("lg")
    st.markdown("##### Previous scenarios this session")
    for past in st.session_state.simulator_history[1:]:
        if past["error"]:
            continue
        with st.container(border=True):
            sc = past["scenario"]
            comp = past["computed"]
            st.markdown(
                f"**{sc['metric']} · {sc['target']} · {sc['change_percent']:+.1f}%** "
                f"— projected revenue: {format_currency(comp['projected_revenue'], style='full')} "
                f"({comp['revenue_delta_pct']:+.1f}%)"
            )