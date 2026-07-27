"""
InsightAI - Shared theme, injected on every page.
Design direction: refined dark sidebar with real navigation hierarchy,
light elevated canvas, indigo accent, tabular numerals for data.
"""

import streamlit as st


# ---------------------------------------------------------------------------
# Color tokens
# ---------------------------------------------------------------------------

SIDEBAR_BG = "#0B0F1A"
SIDEBAR_ACTIVE_BG = "#1A2333"
SIDEBAR_HOVER_BG = "#151B29"
SIDEBAR_TEXT = "#E4E7EC"
SIDEBAR_TEXT_MUTED = "#6B7280"

BG = "#F7F8FA"
CARD_BG = "#FFFFFF"
BORDER = "#E8EAEE"
BORDER_HOVER = "#D8DCE3"

PRIMARY = "#4F46E5"
PRIMARY_HOVER = "#4338CA"
PRIMARY_BG = "#EEF2FF"

TEXT_PRIMARY = "#111827"
TEXT_SECONDARY = "#6B7280"
TEXT_TERTIARY = "#9CA3AF"


# ---------------------------------------------------------------------------
# Semantic colors
# ---------------------------------------------------------------------------

SUCCESS = "#10B981"
SUCCESS_BG = "#ECFDF5"

WARNING = "#F59E0B"
WARNING_BG = "#FFFBEB"
WARNING_BORDER = "#FDE68A"

DANGER = "#EF4444"
DANGER_BG = "#FEF2F2"

INFO = "#6366F1"
INFO_BG = "#EEF2FF"


# ---------------------------------------------------------------------------
# Spacing / radius / shadow
# ---------------------------------------------------------------------------

SPACE_1 = "4px"
SPACE_2 = "8px"
SPACE_3 = "12px"
SPACE_4 = "16px"
SPACE_6 = "24px"
SPACE_8 = "32px"
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
    "High": (SUCCESS, SUCCESS_BG),
    "Medium": (WARNING, WARNING_BG),
    "Low": (DANGER, DANGER_BG),
}


# ---------------------------------------------------------------------------
# Apply global theme
# ---------------------------------------------------------------------------

def apply_theme():

    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap"
            rel="stylesheet"
        >
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <style>

        /* =====================================================
           GLOBAL
        ===================================================== */

        .stApp {{
            background: linear-gradient(135deg, #F8FAFC 0%, #EEF1F6 100%);
        }}

        footer {{
            visibility: hidden;
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

        .mono-num {{
            font-family: 'JetBrains Mono', monospace !important;
            font-variant-numeric: tabular-nums;
        }}

        [data-testid="stHeader"] {{
            visibility: visible !important;
            display: flex !important;
        }}

        header {{
            visibility: visible !important;
        }}


        /* =====================================================
           SIDEBAR
        ===================================================== */

        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #191340 0%, #0B0F1A 55%) !important;
            border-right: 1px solid rgba(255,255,255,0.06);
        }}

        [data-testid="stSidebarCollapsedControl"] {{
            visibility: visible !important;
            display: flex !important;
            opacity: 1 !important;
            z-index: 999999 !important;
            position: fixed !important;
            top: 12px !important;
            left: 12px !important;
        }}

        section[data-testid="stSidebar"] * {{
            color: {SIDEBAR_TEXT} !important;
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
           SIDEBAR NAVIGATION
        ===================================================== */

        section[data-testid="stSidebar"]
        [data-testid="stPageLink-NavLink"] {{
            border-radius: {RADIUS_MD};
            padding: 8px 10px !important;
            margin-bottom: 2px;
            transition: background 120ms ease;
        }}

        section[data-testid="stSidebar"]
        [data-testid="stPageLink-NavLink"]:hover {{
            background: {SIDEBAR_HOVER_BG} !important;
        }}

        section[data-testid="stSidebar"]
        [aria-current="page"] {{
            background: {SIDEBAR_ACTIVE_BG} !important;
            box-shadow: inset 2px 0 0 {PRIMARY}, 0 0 14px rgba(79,70,229,0.35);
            font-weight: 600 !important;
        }}


        /* =====================================================
           SIDEBAR BUTTONS (generic)
        ===================================================== */

        section[data-testid="stSidebar"]
        div[data-testid="column"] button {{
            background: transparent !important;
            border: none !important;
            text-align: left !important;
            font-weight: 400 !important;
            border-radius: {RADIUS_MD} !important;
            transition: background 120ms ease;
        }}

        section[data-testid="stSidebar"]
        div[data-testid="column"] button:hover {{
            background: {SIDEBAR_HOVER_BG} !important;
        }}


        /* =====================================================
           HISTORY ROW - kebab overlays on hover, title spans full width
        ===================================================== */

        div[class*="st-key-history_row"] {{
            position: relative;
            border-radius: {RADIUS_MD};
            margin-bottom: 2px;
            transition: background 120ms ease;
        }}

        div[class*="st-key-history_row"]:hover {{
            background: {SIDEBAR_HOVER_BG};
        }}

        div[class*="st-key-history_row_active"] {{
            background: {SIDEBAR_ACTIVE_BG} !important;
            box-shadow: inset 2px 0 0 {PRIMARY}, 0 0 14px rgba(79,70,229,0.3);
        }}

        div[class*="st-key-history_row"] div[data-testid="stHorizontalBlock"] {{
            align-items: center;
        }}

        div[class*="st-key-history_row"] div[data-testid="column"]:first-child {{
            width: 100% !important;
            flex: 1 1 100% !important;
        }}

        div[class*="st-key-history_row"] div[data-testid="column"]:last-child {{
            position: absolute !important;
            right: 2px;
            top: 50%;
            transform: translateY(-50%);
            width: auto !important;
            opacity: 0;
            transition: opacity 120ms ease;
        }}

        div[class*="st-key-history_row"]:hover div[data-testid="column"]:last-child,
        div[class*="st-key-history_row_active"] div[data-testid="column"]:last-child {{
            opacity: 1;
        }}

        div[class*="st-key-history_row"] button,
        div[class*="st-key-history_row"] [data-testid^="stBaseButton"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: {SIDEBAR_TEXT} !important;
            text-align: left !important;
            font-weight: 400 !important;
            font-size: 13px !important;
            padding: 6px 24px 6px 8px !important;
        }}

        div[class*="st-key-history_row"] button p {{
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            margin: 0 !important;
        }}

        div[class*="st-key-history_row"] div[data-testid="stPopover"] > button {{
            background: transparent !important;
            border: none !important;
            color: {SIDEBAR_TEXT_MUTED} !important;
            min-height: 0 !important;
            padding: 4px 6px !important;
        }}


        /* =====================================================
           SIDEBAR SECTION LABELS
        ===================================================== */

        .sb-label {{
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.06em;
            color: {SIDEBAR_TEXT_MUTED} !important;
            text-transform: uppercase;
            margin: {SPACE_2} 0 {SPACE_2} 4px;
        }}


        /* =====================================================
           MODE SEGMENTED CONTROL
        ===================================================== */

        section[data-testid="stSidebar"]
        div[role="radiogroup"] {{
            background: {SIDEBAR_HOVER_BG};
            border-radius: {RADIUS_MD};
            padding: 3px;
            flex-direction: row !important;
            gap: 0 !important;
        }}

        section[data-testid="stSidebar"]
        div[role="radiogroup"] label > div:first-child,
        section[data-testid="stSidebar"]
        div[role="radiogroup"] label input,
        section[data-testid="stSidebar"]
        div[role="radiogroup"] label svg {{
            display: none !important;
            width: 0 !important;
            height: 0 !important;
            opacity: 0 !important;
        }}

        section[data-testid="stSidebar"]
        div[role="radiogroup"] label {{
            flex: 1;
            text-align: center;
            margin: 0 !important;
            border-radius: 6px;
            padding: 6px 8px !important;
            font-size: 12px !important;
            font-weight: 500 !important;
            color: {SIDEBAR_TEXT_MUTED} !important;
        }}

        section[data-testid="stSidebar"]
        div[role="radiogroup"]
        label:has(input:checked) {{
            background: linear-gradient(135deg, {PRIMARY} 0%, #7C3AED 100%);
            box-shadow: 0 0 10px rgba(124,58,237,0.4);
        }}

        section[data-testid="stSidebar"]
        div[role="radiogroup"]
        label:has(input:checked),
        section[data-testid="stSidebar"]
        div[role="radiogroup"]
        label:has(input:checked) * {{
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }}


        /* =====================================================
           TYPOGRAPHY
        ===================================================== */

        h1 {{
            color: {TEXT_PRIMARY};
            font-weight: 700 !important;
            letter-spacing: -0.02em;
            font-size: 28px !important;
        }}

        h2,
        h3 {{
            color: {TEXT_PRIMARY};
            font-weight: 600 !important;
            letter-spacing: -0.01em;
        }}

        .subtle-caption {{
            color: {TEXT_TERTIARY};
            font-size: 12px;
        }}


        /* =====================================================
           SPACING
        ===================================================== */

        .spacer-sm {{ height: {SPACE_2}; }}
        .spacer-md {{ height: {SPACE_4}; }}
        .spacer-lg {{ height: {SPACE_8}; }}


        /* =====================================================
           METRICS
        ===================================================== */

        div[data-testid="stMetric"] {{
            background-color: {CARD_BG};
            border: 1px solid {BORDER};
            border-radius: {RADIUS_LG};
            padding: {SPACE_4};
            box-shadow: {SHADOW_SM};
            transition: box-shadow 150ms ease, border-color 150ms ease;
        }}

        div[data-testid="stMetric"]:hover {{
            box-shadow: {SHADOW_MD};
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
            font-weight: 700 !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-variant-numeric: tabular-nums;
        }}


        /* =====================================================
           CARDS - flat white, thin border, soft shadow + tiny glow
        ===================================================== */

        div[data-testid="stVerticalBlockBorderWrapper"] > div {{
            background-color: {CARD_BG};
            border-radius: {RADIUS_LG};
            box-shadow: {SHADOW_SM}, 0 0 0 1px rgba(79,70,229,0.04);
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid {BORDER} !important;
            border-radius: {RADIUS_MD} !important;
        }}

        div[data-testid="stPopover"] > div {{
            border-radius: {RADIUS_MD} !important;
            box-shadow: {SHADOW_LG} !important;
            border: 1px solid {BORDER} !important;
        }}


        /* =====================================================
           BUTTONS / INPUTS
        ===================================================== */

        .stButton button {{
            border-radius: {RADIUS_MD};
            font-weight: 500;
            transition: background 120ms ease, box-shadow 120ms ease, opacity 120ms ease;
        }}

        .stButton button[kind="primary"] {{
            background: linear-gradient(135deg, {PRIMARY} 0%, #7C3AED 100%);
            border: none;
        }}

        .stButton button[kind="primary"]:hover {{
            background: linear-gradient(135deg, {PRIMARY_HOVER} 0%, #6D28D9 100%);
            box-shadow: 0 0 16px rgba(124,58,237,0.35);
        }}

        .stButton button:disabled {{
            opacity: 0.5;
        }}

        .stButton button:focus-visible,
        input:focus-visible,
        textarea:focus-visible {{
            outline: 2px solid {PRIMARY} !important;
            outline-offset: 1px;
        }}

        div[data-testid="stTextInput"] input {{
            border-radius: {RADIUS_MD} !important;
            border: 1px solid {BORDER} !important;
        }}

        div[data-testid="stTextInput"] input:focus {{
            border-color: {PRIMARY} !important;
        }}

        div[data-testid="stChatInput"] {{
            border-radius: {RADIUS_MD} !important;
            transition: box-shadow 150ms ease;
        }}

        div[data-testid="stChatInput"]:focus-within {{
            box-shadow: 0 0 0 3px rgba(79,70,229,0.12) !important;
            border-color: {PRIMARY} !important;
        }}


        /* =====================================================
           CHAT MESSAGE CARDS
        ===================================================== */

        .chat-answer-card {{
            background: {CARD_BG};
            border: 1px solid {BORDER};
            border-radius: {RADIUS_LG};
            padding: {SPACE_6};
            box-shadow: {SHADOW_SM};
            margin-bottom: {SPACE_2};
        }}

        .chat-answer-card.is-error {{
            border-left: 3px solid {DANGER};
        }}


        /* =====================================================
           METADATA CHIP ROW
        ===================================================== */

        .chip-row {{
            display: flex;
            flex-wrap: wrap;
            gap: {SPACE_2};
            margin-top: {SPACE_3};
        }}

        div[class*="st-key-chip_row"]
        div[data-testid="stPopover"] > button {{
            background: #F3F4F6 !important;
            border: 1px solid transparent !important;
            border-radius: 999px !important;
            padding: 4px 12px !important;
            font-size: 12px !important;
            font-weight: 500 !important;
            color: {TEXT_SECONDARY} !important;
            min-height: 0 !important;
            transition: background 120ms ease, border-color 120ms ease;
        }}

        div[class*="st-key-chip_row"]
        div[data-testid="stPopover"] > button:hover {{
            background: #E5E7EB !important;
        }}

        div[class*="st-key-chip_row"]
        div[data-testid="stPopover"] > button p {{
            font-size: 12px !important;
            font-weight: 500 !important;
        }}


        /* =====================================================
           GRADIENT CONFIDENCE CHIPS
        ===================================================== */

        div[class*="st-key-conf_chip_high"] div[data-testid="stPopover"] > button {{
            background: linear-gradient(90deg, #10B981, #34D399) !important;
            border: none !important;
            border-radius: 999px !important;
            box-shadow: 0 0 8px rgba(16,185,129,0.35) !important;
            font-weight: 600 !important;
            min-height: 0 !important;
            padding: 4px 12px !important;
        }}

        div[class*="st-key-conf_chip_medium"] div[data-testid="stPopover"] > button {{
            background: linear-gradient(90deg, #F59E0B, #FBBF24) !important;
            border: none !important;
            border-radius: 999px !important;
            font-weight: 600 !important;
            min-height: 0 !important;
            padding: 4px 12px !important;
        }}

        div[class*="st-key-conf_chip_low"] div[data-testid="stPopover"] > button {{
            background: linear-gradient(90deg, #EF4444, #F87171) !important;
            border: none !important;
            border-radius: 999px !important;
            font-weight: 600 !important;
            min-height: 0 !important;
            padding: 4px 12px !important;
        }}

        div[class*="st-key-conf_chip"] div[data-testid="stPopover"] > button p {{
            color: white !important;
            font-size: 12px !important;
        }}


        /* =====================================================
           SKELETON LOADER
        ===================================================== */

        .skeleton-line {{
            background: linear-gradient(90deg, #E8EAEE 25%, #F1F2F5 50%, #E8EAEE 75%);
            background-size: 200% 100%;
            animation: shimmer 1.4s infinite;
            border-radius: 6px;
            height: 14px;
            margin: 6px 0;
        }}

        @keyframes shimmer {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


def spacer(size: str = "md"):
    st.markdown(f'<div class="spacer-{size}"></div>', unsafe_allow_html=True)


def section_label(text: str):
    st.markdown(f'<div class="sb-label">{text}</div>', unsafe_allow_html=True)


def confidence_badge_html(label: str, score: float) -> str:
    fg, bg = CONFIDENCE_COLORS.get(label, (TEXT_SECONDARY, "#F1F5F9"))
    return (
        f'<span style="font-size:11px;font-weight:600;padding:3px {SPACE_2};'
        f'border-radius:{RADIUS_SM};background:{bg};color:{fg};white-space:nowrap;">'
        f'{label} confidence</span>'
    )


def source_tag_html(label: str) -> str:
    return (
        f'<span style="font-size:11px;color:{TEXT_SECONDARY};background:#F1F5F9;'
        f'padding:3px {SPACE_2};border-radius:{RADIUS_SM};margin-right:4px;">{label}</span>'
    )


def banner_html(message: str, kind: str = "warning") -> str:
    palette = {
        "warning": (WARNING_BG, WARNING_BORDER, "#92400E", "warning"),
        "error": (DANGER_BG, DANGER, "#991B1B", "error"),
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


def skeleton_loader():
    st.markdown(
        '<div class="skeleton-line" style="width:55%;"></div>'
        '<div class="skeleton-line" style="width:90%;"></div>'
        '<div class="skeleton-line" style="width:75%;"></div>',
        unsafe_allow_html=True,
    )