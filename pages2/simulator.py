"""
InsightAI - What-If Decision Simulator page.
Wraps agents.simulator.run_decision_simulator (adjust the import path below
to wherever this file actually lives in your project).
"""
import streamlit as st

from core.theme2 import apply_theme, banner_html, spacer

# Adjust this import to the actual module path for run_decision_simulator
from agents.simulator.decision_simulator import run_decision_simulator

st.set_page_config(page_title="InsightAI - Simulator", page_icon="📊", layout="wide")
apply_theme()

st.title("What-if simulator")
st.caption("Straight-line projections from real current data — no elasticity modeled")

if "simulator_history" not in st.session_state:
    st.session_state.simulator_history = []

question = st.text_input(
    "Scenario",
    placeholder="What if we increase Beverages price by 10%?",
    label_visibility="collapsed",
)
run_clicked = st.button("Run simulation", type="primary")

if run_clicked and question.strip():
    with st.spinner("Computing projection..."):
        result = run_decision_simulator(question)
    st.session_state.simulator_history.insert(0, result)

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
            st.metric("Current revenue", f"${computed['current_revenue']:,.0f}")
        with col2:
            st.metric(
                "Projected revenue",
                f"${computed['projected_revenue']:,.0f}",
                f"{computed['revenue_delta_pct']:+.1f}%",
            )
        with col3:
            st.metric("Current avg. unit price", f"${computed['current_avg_price']:.2f}")

        st.markdown("##### Analysis")
        st.markdown(latest["answer"].replace("$", "\\$"))

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
                f"— projected revenue: ${comp['projected_revenue']:,.0f} "
                f"({comp['revenue_delta_pct']:+.1f}%)"
            )