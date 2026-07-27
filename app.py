"""
InsightAI - Navigation controller only. All actual page logic lives in
chat.py and pages/*.py - nothing else should execute in this file.
"""
import streamlit as st
from core.theme2 import apply_theme

st.set_page_config(
    page_title="InsightAI",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_theme()

pg = st.navigation([
    st.Page("chat2.py", title="Chat", icon=":material/forum:", default=True),
    st.Page("pages2/dashboard.py", title="Dashboard", icon=":material/dashboard:"),
    st.Page("pages2/executive_report.py", title="Executive report", icon=":material/description:"),
    st.Page("pages2/history.py", title="History", icon=":material/history:"),
    st.Page("pages2/simulator.py", title="Simulator", icon=":material/calculate:"),
])
pg.run()