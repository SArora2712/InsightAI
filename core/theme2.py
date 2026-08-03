"""
InsightAI - Shared theme, injected on every page.
Design direction: light navy sidebar, light elevated canvas,
navy + gold brand palette (gold = small accents only).
"""

import html
import streamlit as st


# ---------------------------------------------------------------------------
# Color tokens
# ---------------------------------------------------------------------------

SIDEBAR_BG          = "#0B0F19"
SIDEBAR_ACTIVE_BG   = "#1E1B4B"
SIDEBAR_HOVER_BG    = "#1F2937"
SIDEBAR_TEXT        = "#F3F4F6"
SIDEBAR_TEXT_MUTED  = "#9CA3AF"
SIDEBAR_TEXT_DIM    = "#6B7280"

SIDEBAR_CARD        = "#111827"
SIDEBAR_CARD_HOVER  = "#172033"
SIDEBAR_BORDER      = "rgba(255,255,255,0.07)"
SIDEBAR_ACCENT      = "#B8935A"
SIDEBAR_ACCENT_BG   = "rgba(184,147,90,0.16)"
SIDEBAR_MUTED       = "#64748B"

BG                  = "#F7F8FA"
CARD_BG             = "#FFFFFF"
BORDER              = "#E8EAEE"
BORDER_HOVER        = "#D8DCE3"

PRIMARY             = "#10203D"
PRIMARY_HOVER       = "#1B2E55"
PRIMARY_BG          = "#EEF1F6"
PRIMARY_SOFT        = "rgba(16,32,61,0.12)"

GOLD                = "#B8935A"
GOLD_SOFT           = "rgba(184,147,90,0.18)"

TEXT_PRIMARY        = "#10203D"
TEXT_SECONDARY      = "#5A6472"
TEXT_TERTIARY       = "#8A93A3"


# ---------------------------------------------------------------------------
# Semantic colors
# ---------------------------------------------------------------------------

SUCCESS        = "#10B981"
SUCCESS_BG     = "#ECFDF5"

WARNING        = "#F59E0B"
WARNING_BG     = "#FFFBEB"
WARNING_BORDER = "#FDE68A"

DANGER         = "#EF4444"
DANGER_BG      = "#FEF2F2"

INFO           = "#10203D"
INFO_BG        = "#EEF1F6"


# ---------------------------------------------------------------------------
# Spacing / radius / shadow
# ---------------------------------------------------------------------------

SPACE_1  = "4px"
SPACE_2  = "8px"
SPACE_3  = "12px"
SPACE_4  = "16px"
SPACE_6  = "24px"
SPACE_8  = "32px"
SPACE_12 = "48px"

RADIUS_SM = "6px"
RADIUS_MD = "8px"
RADIUS_LG = "14px"

SHADOW_SM = (
    "0 1px 2px rgba(16,24,40,0.04), "
    "0 1px 1px rgba(16,24,40,0.03)"
)
SHADOW_MD = "0 4px 16px rgba(16,24,40,0.08)"
SHADOW_LG = "0 8px 24px rgba(16,24,40,0.12)"


# ---------------------------------------------------------------------------
# Confidence colors
# ---------------------------------------------------------------------------

CONFIDENCE_COLORS = {
    "High":   (SUCCESS, SUCCESS_BG),
    "Medium": (WARNING, WARNING_BG),
    "Low":    (DANGER, DANGER_BG),
}


# ---------------------------------------------------------------------------
# Apply global theme
# ---------------------------------------------------------------------------

def apply_theme():

    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link
            href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap"
            rel="stylesheet"
        >
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap');

        /* =====================================================
           GLOBAL
        ===================================================== */

        html, body, [data-testid="stAppViewContainer"], .stApp {{
            height: auto !important;
            min-height: 100vh !important;
            overflow-y: auto !important;
        }}

        section.main {{
            height: auto !important;
            overflow-y: visible !important;
        }}

        .block-container {{
            padding-top: 2rem !important;
            padding-bottom: 3rem !important;
            padding-left: 3rem !important;
            padding-right: 3rem !important;
            height: auto !important;
            overflow: visible !important;
            max-width: 1400px !important;
        }}

        [data-testid="stVerticalBlock"] {{
            height: auto !important;
            overflow: visible !important;
        }}

        .stApp,
        section.main,
        .block-container {{
            background: #F7F8FA !important;
        }}

        /* =====================================================
           ALERTS (st.info / st.warning / st.error / st.success)
        ===================================================== */

        div[data-testid="stAlert"] {{
            border-radius: 8px !important;
            border: none !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        }}

        div[data-testid="stAlertContainer"][kind="info"] {{
            background: #EEF1F6 !important;
            border-left: 3px solid #10203D !important;
            color: #1A2B4A !important;
        }}

        div[data-testid="stAlertContainer"][kind="warning"] {{
            background: #FBF3E7 !important;
            border-left: 3px solid #B8935A !important;
            color: #6B4A1F !important;
        }}

        div[data-testid="stAlertContainer"][kind="error"] {{
            background: #FEF2F2 !important;
            border-left: 3px solid #D64545 !important;
            color: #8A2424 !important;
        }}

        div[data-testid="stAlertContainer"][kind="success"] {{
            background: #ECFDF5 !important;
            border-left: 3px solid #10B981 !important;
            color: #0E6B47 !important;
        }}

        div[data-testid="stAlert"] p {{
            color: inherit !important;
        }}

        footer, #MainMenu, .stDeployButton {{
            display: none !important;
        }}

        header[data-testid="stHeader"] {{
            background: transparent !important;
            height: 0px !important;
            min-height: 0px !important;
        }}

        section.main > div {{
            padding-top: 0 !important;
        }}

        [data-testid="stVerticalBlock"] > div:first-child {{
            margin-top: 0 !important;
            padding-top: 0 !important;
        }}

        .stApp,
        .stApp p,
        .stApp span,
        .stApp label,
        .stApp input,
        .stApp textarea,
        .stApp button,
        .stApp select {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont,
                         'Segoe UI', sans-serif;
        }}

        [data-testid="stIconMaterial"] {{
            font-family: 'Material Symbols Rounded' !important;
        }}

        .mono-num,
        .confidence-score,
        .metric-value {{
            font-family: 'IBM Plex Mono', monospace !important;
            font-variant-numeric: tabular-nums;
        }}


        /* =====================================================
           TYPOGRAPHY
        ===================================================== */

        h1 {{
            font-size: 28px !important;
            font-weight: 600 !important;
            letter-spacing: -0.01em;
            font-family: 'Fraunces', Georgia, 'Times New Roman', serif !important;
            color: {PRIMARY} !important;
        }}

        h2, h3 {{
            color: {TEXT_PRIMARY};
            font-weight: 600 !important;
            letter-spacing: -0.01em;
            font-family: 'Fraunces', Georgia, 'Times New Roman', serif !important;
        }}

        .subtle-caption {{
            color: {TEXT_TERTIARY};
            font-size: 12px;
        }}

        div[data-testid="stMarkdown"] h5,
        .stMarkdown h5 {{
            font-size: 17px !important;
            font-weight: 600 !important;
            color: {PRIMARY} !important;
            margin-bottom: 12px !important;
            letter-spacing: -0.01em;
        }}


        /* =====================================================
           SPACING HELPERS
        ===================================================== */

        .spacer-sm {{ height: {SPACE_2}; }}
        .spacer-md {{ height: {SPACE_4}; }}
        .spacer-lg {{ height: {SPACE_8}; }}


        /* =====================================================
           METRICS
        ===================================================== */

        div[data-testid="stMetric"] {{
            background: #FFFFFF !important;
            border: 1px solid {BORDER} !important;
            border-left: 3px solid {GOLD} !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 2px rgba(16, 32, 61, 0.04) !important;
            padding: 18px 16px !important;
        }}

        div[data-testid="stMetric"]:hover {{
            box-shadow: 0 6px 24px rgba(16,32,61,0.10) !important;
            border-color: {BORDER_HOVER};
        }}

        div[data-testid="stMetricLabel"] {{
            color: {TEXT_SECONDARY} !important;
            font-size: 12px !important;
            font-weight: 500 !important;
        }}

        div[data-testid="stMetricValue"] {{
            color: {TEXT_PRIMARY} !important;
            font-size: 24px !important;
            font-weight: 600 !important;
            font-family: 'IBM Plex Mono', monospace !important;
            font-variant-numeric: tabular-nums;
        }}


        /* =====================================================
           CARDS
        ===================================================== */

        div[data-testid="stVerticalBlockBorderWrapper"] > div {{
            background: #FFFFFF !important;
            border-radius: 8px !important;
            border: 1px solid #E4E7EC !important;
            border-left: 3px solid {GOLD} !important;
            box-shadow: 0 1px 2px rgba(16,32,61,0.04) !important;
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid {BORDER} !important;
            border-radius: 8px !important;
            background: #F7F8FA !important;
        }}


        /* =====================================================
           BUTTONS / INPUTS
        ===================================================== */

        .stButton button {{
            border-radius: 6px !important;
            border: 1px solid {PRIMARY};
            background: {PRIMARY};
            color: #ffffff;
            font-weight: 500;
            letter-spacing: 0.01em;
            transition: all 0.15s ease;
        }}

        .stButton button:hover {{
            background: #16305C !important;
            border-color: {GOLD} !important;
            transform: translateY(-1px);
        }}

        .stButton button[kind="primary"] {{
            background: {PRIMARY} !important;
            border: 1px solid {PRIMARY} !important;
            box-shadow: 0 4px 14px rgba(16, 32, 61, 0.20) !important;
            color: white !important;
        }}

        .stButton button[kind="primary"]:hover {{
            background: #16305C !important;
            border: 1px solid {GOLD} !important;
            box-shadow: 0 0 0 3px {GOLD_SOFT}, 0 6px 16px rgba(16,32,61,0.18) !important;
        }}

        div[data-testid="stTextInput"] input {{
            border-radius: 8px !important;
            border: 1.5px solid #D8DCE3 !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        }}

        div[data-testid="stTextInput"] input:focus {{
            border-color: {GOLD} !important;
            box-shadow: 0 0 0 3px {GOLD_SOFT} !important;
        }}


        /* =====================================================
           CHAT INPUT
        ===================================================== */

        div[data-testid="stChatInput"] {{
            background: #FFFFFF !important;
            border: 1.5px solid #D8DCE3 !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 2px rgba(16,32,61,0.04) !important;
        }}

        div[data-testid="stChatInput"]:focus-within {{
            border-color: {GOLD} !important;
            box-shadow: 0 0 0 3px {GOLD_SOFT} !important;
        }}

        div[data-testid="stChatInput"] * {{
            outline: none !important;
        }}


        /* =====================================================
           CHAT MESSAGES
        ===================================================== */

        .insight-card,
        .ai-answer-card {{
            background: #FFFFFF !important;
            border: 1px solid #E4E7EC !important;
            border-left: 3px solid {GOLD} !important;
            border-radius: 8px !important;
            padding: 20px 24px !important;
            box-shadow: 0 1px 2px rgba(16,32,61,0.04) !important;
        }}

        .ai-answer-card {{
            margin-bottom: 6px !important;
        }}

        div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"])
        [data-testid="stChatMessageContent"] {{
            background: #FFFFFF !important;
            border: 1px solid #E4E7EC !important;
            border-left: 3px solid {GOLD} !important;
            border-radius: 8px !important;
            padding: 20px 24px !important;
            box-shadow: 0 1px 2px rgba(16,32,61,0.04) !important;
            max-width: 100% !important;
        }}

        div[data-testid="stChatMessage"] {{
            width: 100% !important;
            margin-bottom: 12px !important;
        }}

        div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
            display: flex !important;
            flex-direction: row-reverse !important;
            justify-content: flex-start !important;
            gap: 8px !important;
        }}

        div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
        [data-testid="stChatMessageContent"] {{
            background: #F1F5F9 !important;
            border: 1px solid {BORDER} !important;
            border-radius: 16px 16px 4px 16px !important;
            padding: 12px 16px !important;
            max-width: 70% !important;
            margin-left: auto !important;
        }}


        /* =====================================================
           CHIPS
        ===================================================== */

        div[class*="st-key-chip_row"] div[data-testid="stPopover"] > button {{
            background: #F1F5F9 !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 999px !important;
            padding: 4px 12px !important;
            font-size: 12px !important;
            font-weight: 500 !important;
            color: {TEXT_SECONDARY} !important;
            min-height: 28px !important;
        }}

        div[class*="st-key-conf_chip_high"] div[data-testid="stPopover"] > button {{
            background: linear-gradient(90deg, #10B981, #34D399) !important;
            border: none !important;
            border-radius: 999px !important;
            box-shadow: inset 3px 0 0 {GOLD}, 0 0 8px rgba(16,185,129,0.35) !important;
            font-weight: 600 !important;
            color: white !important;
        }}

        div[class*="st-key-conf_chip_medium"] div[data-testid="stPopover"] > button {{
            background: linear-gradient(90deg, #F59E0B, #FBBF24) !important;
            border: none !important;
            border-radius: 999px !important;
            box-shadow: inset 3px 0 0 {GOLD} !important;
            font-weight: 600 !important;
            color: white !important;
        }}

        div[class*="st-key-conf_chip_low"] div[data-testid="stPopover"] > button {{
            background: linear-gradient(90deg, #EF4444, #F87171) !important;
            border: none !important;
            border-radius: 999px !important;
            box-shadow: inset 3px 0 0 {GOLD} !important;
            font-weight: 600 !important;
            color: white !important;
        }}

        div[class*="st-key-conf_chip"] div[data-testid="stPopover"] > button p {{
            color: white !important;
            font-size: 12px !important;
        }}


        /* =====================================================
           SIDEBAR BASE
        ===================================================== */

        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #0F172A 0%, #020617 100%) !important;
            border-right: 1px solid rgba(255,255,255,0.06) !important;
        }}

        section[data-testid="stSidebar"] > div {{
            padding-left: 14px !important;
            padding-right: 14px !important;
        }}

        div[data-testid="stSidebarHeader"] {{
            display: none !important;
        }}

        div[data-testid="stSidebarContent"] {{
            padding-top: 0 !important;
        }}

        section[data-testid="stSidebar"] .stCaption,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] small {{
            color: {SIDEBAR_TEXT_MUTED} !important;
        }}

        section[data-testid="stSidebar"] hr {{
            border-color: rgba(255,255,255,0.07) !important;
            margin: {SPACE_4} 0;
        }}


        /* =====================================================
           PAGE NAVIGATION (restored + styled)
        ===================================================== */

        section[data-testid="stSidebarNav"] {{
            display: block !important;
            padding-top: 4px !important;
            margin-bottom: 8px !important;
        }}

        section[data-testid="stSidebarNav"] a {{
            color: {SIDEBAR_TEXT_MUTED} !important;
            border-radius: 8px !important;
            padding: 8px 12px !important;
            font-size: 13.5px !important;
            font-weight: 500 !important;
            margin: 2px 0 !important;
        }}

        section[data-testid="stSidebarNav"] a:hover {{
            background: rgba(255,255,255,0.05) !important;
            color: #E2E8F0 !important;
        }}

        section[data-testid="stSidebarNav"] a[aria-current="page"],
        section[data-testid="stSidebarNav"] [aria-current="page"],
        section[data-testid="stSidebar"] [aria-current="page"] {{
            background: {SIDEBAR_ACCENT_BG} !important;
            color: {SIDEBAR_TEXT} !important;
            box-shadow: inset 3px 0 0 {SIDEBAR_ACCENT} !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
        }}


        /* =====================================================
           BRAND
        ===================================================== */

        .ia-brand {{
            padding: 6px 4px 14px 4px !important;
            margin-bottom: 6px !important;
        }}

        .ia-brand-title {{
            font-size: 20px !important;
            font-weight: 700 !important;
            letter-spacing: -0.03em !important;
            color: {SIDEBAR_TEXT} !important;
            line-height: 1.2 !important;
        }}

        .ia-brand-title span {{
            color: {SIDEBAR_ACCENT} !important;
        }}

        .ia-brand-mark {{
            color: {SIDEBAR_ACCENT} !important;
            margin-right: 6px !important;
            font-size: 18px !important;
        }}

        .ia-brand-subtitle {{
            margin-top: 3px !important;
            font-size: 10px !important;
            font-weight: 600 !important;
            color: {SIDEBAR_TEXT_MUTED} !important;
            letter-spacing: 0.10em !important;
            text-transform: uppercase !important;
        }}


        /* =====================================================
           SECTION LABELS
        ===================================================== */

        .sb-label,
        .ia-section-label {{
            font-size: 10px !important;
            font-weight: 600 !important;
            letter-spacing: 0.10em !important;
            color: {SIDEBAR_MUTED} !important;
            text-transform: uppercase !important;
            margin: 18px 0 8px 4px !important;
        }}


        /* =====================================================
           MODE SWITCHER (no red dot)
        ===================================================== */

        section[data-testid="stSidebar"] div[role="radiogroup"] {{
            background: #1E293B !important;
            border-radius: 12px !important;
            padding: 4px !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
        }}

        section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child,
        section[data-testid="stSidebar"] div[role="radiogroup"] label input,
        section[data-testid="stSidebar"] div[role="radiogroup"] label svg {{
            display: none !important;
            width: 0 !important;
            height: 0 !important;
            opacity: 0 !important;
        }}

        section[data-testid="stSidebar"] div[role="radiogroup"] label {{
            flex: 1 !important;
            text-align: center !important;
            border-radius: 9px !important;
            padding: 9px 10px !important;
            font-size: 12.5px !important;
            font-weight: 500 !important;
            color: {SIDEBAR_TEXT_MUTED} !important;
        }}

        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
            background: {GOLD} !important;
            color: {PRIMARY} !important;
            font-weight: 600 !important;
            box-shadow: 0 0 14px {GOLD_SOFT} !important;
        }}

        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked),
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) * {{
            color: {PRIMARY} !important;
        }}

        section[data-testid="stSidebar"] div[role="radiogroup"] label:not(:has(input:checked)):hover {{
            background: rgba(255,255,255,0.04) !important;
            color: #E2E8F0 !important;
        }}


        /* =====================================================
           HISTORY ROWS
        ===================================================== */

        div[class*="st-key-history_row"] {{
            border-radius: 8px !important;
            margin: 1px 2px !important;
        }}

        div[class*="st-key-history_row"]:hover {{
            background: rgba(255,255,255,0.035) !important;
        }}

        div[class*="st-key-history_row_active"] {{
            background: {SIDEBAR_ACCENT_BG} !important;
            box-shadow: inset 3px 0 0 {SIDEBAR_ACCENT} !important;
            border-radius: 8px !important;
        }}

        div[class*="st-key-history_row"] button,
        div[class*="st-key-history_row"] [data-testid^="stBaseButton"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: {SIDEBAR_TEXT_MUTED} !important;
            text-align: left !important;
            font-size: 12.5px !important;
            font-weight: 500 !important;
            padding: 8px 12px !important;
            width: 100% !important;
            border-radius: 7px !important;
        }}

        div[class*="st-key-history_row_active"] button {{
            color: {SIDEBAR_TEXT} !important;
            font-weight: 600 !important;
        }}

        div[class*="st-key-history_row"] button p {{
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            margin: 0 !important;
        }}


        /* =====================================================
           SIDEBAR PRIMARY BUTTON
        ===================================================== */

        section[data-testid="stSidebar"] button[kind="primary"] {{
            width: 100% !important;
            min-height: 40px !important;
            background: {GOLD} !important;
            border: 1px solid {GOLD} !important;
            border-radius: 6px !important;
            color: {PRIMARY} !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 12px rgba(184,147,90,0.30) !important;
        }}

        section[data-testid="stSidebar"] button[kind="primary"] p {{
            color: {PRIMARY} !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            margin: 0 !important;
        }}

        section[data-testid="stSidebar"] button[kind="primary"]:hover {{
            background: #C7A56B !important;
            border: 1px solid #C7A56B !important;
            box-shadow: 0 0 0 3px {GOLD_SOFT}, 0 6px 16px rgba(184,147,90,0.35) !important;
        }}


        /* =====================================================
           EXAMPLE QUESTION BUTTONS
        ===================================================== */

        div[class*="st-key-ex_"] .stButton button {{
            background: #FFFFFF !important;
            border: 1px solid {BORDER} !important;
            border-radius: 12px !important;
            color: {TEXT_SECONDARY} !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            padding: 14px 12px !important;
            min-height: 64px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
            white-space: normal !important;
            line-height: 1.35 !important;
        }}

        div[class*="st-key-ex_"] .stButton button:hover {{
            border-color: {PRIMARY} !important;
            box-shadow: 0 4px 12px {PRIMARY_SOFT} !important;
            color: {PRIMARY} !important;
        }}


        /* =====================================================
           ACCESSIBILITY: visible focus indicator
           (restores a clear :focus-visible outline so keyboard
           navigation is obvious; mouse click styling unchanged)
        ===================================================== */

        button:focus-visible,
        a:focus-visible,
        input:focus-visible,
        textarea:focus-visible,
        select:focus-visible,
        [data-testid="stBaseButton"]:focus-visible,
        [data-testid="stChatInput"] *:focus-visible {{
            outline: 2px solid {PRIMARY} !important;
            outline-offset: 2px !important;
            box-shadow: 0 0 0 3px {PRIMARY_SOFT} !important;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )

    # Fallback JS for user message alignment
    st.markdown(
        """
        <script>
        function forceAlignUserMessages() {
            const docs = [document, window.parent.document];
            docs.forEach(doc => {
                const messages = doc.querySelectorAll('[data-testid="stChatMessage"]');
                messages.forEach(msg => {
                    const isUser = msg.querySelector('[data-testid="stChatMessageAvatarUser"]')
                                || msg.querySelector('img[alt="user"]');
                    if (isUser) {
                        msg.style.setProperty('display', 'flex', 'important');
                        msg.style.setProperty('flex-direction', 'row-reverse', 'important');
                        msg.style.setProperty('justify-content', 'flex-start', 'important');

                        const content = msg.querySelector('[data-testid="stChatMessageContent"]');
                        if (content) {
                            content.style.setProperty('background', '#F1F5F9', 'important');
                            content.style.setProperty('border', '1px solid #E8EAEE', 'important');
                            content.style.setProperty('border-radius', '16px 16px 4px 16px', 'important');
                            content.style.setProperty('padding', '12px 16px', 'important');
                            content.style.setProperty('max-width', '70%', 'important');
                            content.style.setProperty('margin-left', 'auto', 'important');
                        }
                    }
                });
            });
        }

        function ensureSidebarBrand() {
            const docs = [document, window.parent.document];
            docs.forEach(doc => {
                const content = doc.querySelector('[data-testid="stSidebarContent"]');
                if (!content) return;
                if (content.querySelector('.ia-brand')) return;
                const nav = doc.querySelector('[data-testid="stSidebarNav"]');
                const div = doc.createElement('div');
                div.className = 'ia-brand';
                div.innerHTML =
                    '<div class="ia-brand-title">' +
                    '<span class="ia-brand-mark">✦</span> Insight<span>AI</span>' +
                    '</div>' +
                    '<div class="ia-brand-subtitle">Business Intelligence</div>';
                if (nav) content.insertBefore(div, nav);
                else content.appendChild(div);
            });
        }

        forceAlignUserMessages();
        ensureSidebarBrand();
        const observer = new MutationObserver(() => {
            forceAlignUserMessages();
            ensureSidebarBrand();
        });
        observer.observe(window.parent.document.body, { childList: true, subtree: true });
        setInterval(() => {
            forceAlignUserMessages();
            ensureSidebarBrand();
        }, 1000);
        </script>
        """,
        unsafe_allow_html=True,
    )


def spacer(size: str = "md"):
    st.markdown(f'<div class="spacer-{size}"></div>', unsafe_allow_html=True)


def section_label(text: str):
    st.markdown(f'<div class="sb-label">{text}</div>', unsafe_allow_html=True)


def render_sidebar_brand():
    st.markdown(
        """
        <div class="ia-brand">
            <div class="ia-brand-title">
                <span class="ia-brand-mark">✦</span> Insight<span>AI</span>
            </div>
            <div class="ia-brand-subtitle">Business Intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def confidence_badge_html(label: str, score: float) -> str:
    label = html.escape(str(label))
    score_txt = f"{score:.2f}"
    if label == "High":
        return (
            f'<span style="font-size:11px;font-weight:600;padding:4px 12px;'
            f'border-radius:999px;background:linear-gradient(90deg,#10B981,#34D399);'
            f'color:white;box-shadow:inset 3px 0 0 #B8935A,0 0 8px rgba(16,185,129,0.35);'
            f'font-family:\'IBM Plex Mono\',monospace;">'
            f'{label} · {score_txt}</span>'
        )
    elif label == "Medium":
        return (
            f'<span style="font-size:11px;font-weight:600;padding:4px 12px;'
            f'border-radius:999px;background:linear-gradient(90deg,#F59E0B,#FBBF24);'
            f'color:white;box-shadow:inset 3px 0 0 #B8935A;'
            f'font-family:\'IBM Plex Mono\',monospace;">'
            f'{label} · {score_txt}</span>'
        )
    else:
        return (
            f'<span style="font-size:11px;font-weight:600;padding:4px 12px;'
            f'border-radius:999px;background:linear-gradient(90deg,#EF4444,#F87171);'
            f'color:white;box-shadow:inset 3px 0 0 #B8935A;'
            f'font-family:\'IBM Plex Mono\',monospace;">'
            f'{label} · {score_txt}</span>'
        )


def source_tag_html(label: str) -> str:
    return (
        f'<span style="font-size:11px;color:{TEXT_SECONDARY};background:#F1F5F9;'
        f'padding:3px {SPACE_2};border-radius:{RADIUS_SM};margin-right:4px;">{label}</span>'
    )


def banner_html(message: str, kind: str = "warning") -> str:
    palette = {
        "warning": (WARNING_BG, WARNING_BORDER, "#92400E", "warning"),
        "error":   (DANGER_BG, DANGER, "#991B1B", "error"),
    }
    bg, border, text, icon = palette.get(kind, palette["warning"])
    return (
        f'<div style="background:{bg};border:1px solid {border};border-radius:{RADIUS_MD};'
        f'padding:{SPACE_3} 14px;margin-top:{SPACE_3};font-size:13px;color:{text};'
        f'display:flex;gap:8px;align-items:flex-start;">'
        f'<span class="material-symbols-rounded" style="font-size:16px;">{icon}</span>'
        f'<span>{message}</span></div>'
    )


def severity_icon(label: str) -> str:
    return {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(label, "⚪")


def mono(value: str) -> str:
    return f'<span class="mono-num">{value}</span>'