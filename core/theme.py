"""
InsightAI - Shared theme, injected on every page.
Linear/Vercel/Notion-inspired: dark sidebar, light elevated cards, blue accent.
"""
import streamlit as st

NAVY = "#0B1120"
BLUE = "#2563EB"
BG = "#F8FAFC"
CARD_BG = "#FFFFFF"
BORDER = "#E2E8F0"
TEXT_PRIMARY = "#0F172A"
TEXT_SECONDARY = "#64748B"
GREEN = "#16A34A"
RED = "#DC2626"
AMBER = "#F59E0B"


def apply_theme():
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <style>
    .stApp *:not([data-testid="stIconMaterial"]),
        [data-testid="stAppViewContainer"] *:not([data-testid="stIconMaterial"]) {{
            font-family: 'Inter', -apple-system, sans-serif !important;
        }}

        [data-testid="stIconMaterial"] {{
            font-family: 'Material Symbols Rounded' !important;
        }}

    [data-testid="stHeader"] {{ display: none; }}
    footer {{ visibility: hidden; }}

    .stApp {{ background-color: {BG}; }}

/* Recents expander styled as a plain section header, not a bordered box */
    section[data-testid="stSidebar"] div[data-testid="stExpander"] {{
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stExpander"] summary {{
        font-weight: 500;
        font-size: 13px;
        color: #94A3B8 !important;
        padding-left: 0 !important;
    }}

    /* Ghost-style rows for history items - no border, subtle hover */
    section[data-testid="stSidebar"] div[data-testid="column"] button {{
        background: transparent !important;
        border: none !important;
        text-align: left !important;
        font-weight: 400 !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="column"] button:hover {{
        background: rgba(255,255,255,0.08) !important;
    }}

    /* Kebab menu button - subtle at rest, clearer on row hover */
    section[data-testid="stSidebar"] div[data-testid="stPopover"] > button {{
        opacity: 0.4;
        background: transparent !important;
        border: none !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"]:hover div[data-testid="stPopover"] > button {{
        opacity: 1;
    }}
    
    h1, h2, h3 {{ color: {TEXT_PRIMARY}; font-weight: 600 !important; letter-spacing: -0.01em; }}

    div[data-testid="stMetric"] {{
        background-color: {CARD_BG}; border: 0.5px solid {BORDER};
        border-radius: 12px; padding: 16px; box-shadow: 0 1px 2px rgba(15,23,42,0.04);
    }}
    div[data-testid="stMetricLabel"] {{ color: {TEXT_SECONDARY} !important; font-size: 12px !important; }}
    div[data-testid="stMetricValue"] {{ color: {TEXT_PRIMARY} !important; font-size: 22px !important; font-weight: 600 !important; }}

    div[data-testid="stVerticalBlockBorderWrapper"] > div {{ background-color: {CARD_BG}; border-radius: 12px; }}
    div[data-testid="stExpander"] {{ border: 0.5px solid {BORDER} !important; border-radius: 12px !important; }}

    .stButton button {{ border-radius: 8px; font-weight: 500; }}
    .stButton button[kind="primary"] {{ background-color: {BLUE}; border: none; }}
    </style>
    """, unsafe_allow_html=True)

def confidence_badge_html(label: str, score: float) -> str:
    colors = {
        "High": (GREEN, "#DCFCE7", "#166534"),
        "Medium": (AMBER, "#FEF3C7", "#92400E"),
        "Low": (RED, "#FEE2E2", "#991B1B"),
    }
    _, bg, text = colors.get(label, (TEXT_SECONDARY, "#F1F5F9", TEXT_SECONDARY))
    return (
        f'<span style="font-size:11px;font-weight:500;padding:2px 8px;'
        f'border-radius:6px;background:{bg};color:{text};">{label} confidence</span>'
    )


def source_tag_html(label: str) -> str:
    return (
        f'<span style="font-size:11px;color:{TEXT_SECONDARY};background:#F1F5F9;'
        f'padding:2px 8px;border-radius:6px;margin-right:4px;">{label}</span>'
    )