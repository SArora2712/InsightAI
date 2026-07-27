import streamlit as st

st.set_page_config(
    page_title="InsightAI",
    layout="wide",
    initial_sidebar_state="expanded"
)

pg = st.navigation([
    st.Page("test_sidebar.py", title="Test", default=True),
])

pg.run()