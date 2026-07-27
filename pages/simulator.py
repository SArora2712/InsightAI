"""
InsightAI - What-If Decision Simulator page.
Wraps agents.simulator.run_decision_simulator (adjust the import path below
to wherever this file actually lives in your project).
"""
import streamlit as st

from core.theme import apply_theme, TEXT_SECONDARY, AMBER

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

        st.markdown(
            f'<div style="background:#FEF3C7;border:0.5px solid #FDE68A;border-radius:8px;'
            f'padding:10px 14px;margin-top:12px;font-size:13px;color:#92400E;">'
            f'⚠️ This is a straight-line projection holding all else constant — it does not model '
            f'price elasticity, customer behavior change, or competitive response.</div>',
            unsafe_allow_html=True,
        )

if len(st.session_state.simulator_history) > 1:
    st.markdown("<br>", unsafe_allow_html=True)
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
