"""
InsightAI - Navigation controller only. All actual page logic lives in
chat.py and pages/*.py - nothing else should execute in this file.
"""
import streamlit as st
from core.theme2 import apply_theme
from core.auth import is_authenticated, is_admin, logout
from core.landing import (
    current_view,
    render_landing,
    render_auth_view,
    LANDING_VIEW,
    AUTH_VIEW,
    APP_VIEW,
)

st.set_page_config(
    page_title="InsightAI · Insights Chat",
    page_icon="logo/favicon.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    [data-testid="stToolbar"] {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}
</style>
""", unsafe_allow_html=True)
apply_theme()

# Entry experience: land on the marketing/landing view; only once the user
# picks "Try the demo" (guest) or signs in do we reach the in-app views.
# An authenticated session is always routed to the app view.
view = current_view()
if view == AUTH_VIEW:
    render_auth_view()
    st.stop()
if view != APP_VIEW:
    render_landing()
    st.stop()

with st.sidebar:
    if st.session_state.get("role") == "guest":
        st.markdown(
            (
                "<div style='font-size:12px;color:#64748B;padding:2px 6px 12px;'>"
                "Viewing as <b>guest</b> · admin pages are locked</div>"
            ),
            unsafe_allow_html=True,
        )
    if st.button(
        "Sign out",
        key="sign_out_btn",
        use_container_width=True,
        icon=":material/logout:",
    ):
        logout()
        st.session_state["view"] = LANDING_VIEW
        st.rerun()

pages = [
    st.Page("chat2.py", title="Chat", icon=":material/forum:", default=True),
    st.Page("pages2/dashboard.py", title="Dashboard", icon=":material/dashboard:"),
    st.Page("pages2/executive_report.py", title="Executive report", icon=":material/description:"),
    st.Page("pages2/history.py", title="History", icon=":material/history:"),
    st.Page("pages2/simulator.py", title="Simulator", icon=":material/calculate:"),
]
if is_admin():
    pages.append(
        st.Page("pages2/performance_monitor.py", title="Performance", icon=":material/speed:")
    )
pg = st.navigation(pages)
pg.run()