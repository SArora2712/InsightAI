"""
InsightAI - Shared theme, injected on every page.
Design direction: light elevated canvas, navy sidebar,
teal product accent. Single source of truth for design tokens.
"""

import html
import pathlib
import streamlit as st


# ---------------------------------------------------------------------------
# Brand / core
# ---------------------------------------------------------------------------

NAVY                = "#10203D"
NAVY_DARK           = "#0B1A33"
NAVY_SOFT           = "rgba(16,32,61,0.12)"

TEAL                = "#14B8A6"
TEAL_SOFT           = "rgba(20,184,166,0.16)"

PRIMARY             = NAVY
PRIMARY_HOVER       = "#1B2E55"
PRIMARY_BG          = "#EEF4F8"
PRIMARY_SOFT        = NAVY_SOFT


# ---------------------------------------------------------------------------
# Canvas / structure
# ---------------------------------------------------------------------------

BG                  = "#F7F9FC"
CARD_BG             = "#FFFFFF"
BORDER              = "#E5EAF1"
BORDER_HOVER        = "#CBD5E1"

TEXT_PRIMARY        = NAVY
TEXT_SECONDARY      = "#64748B"
TEXT_TERTIARY       = "#94A3B8"


# ---------------------------------------------------------------------------
# Sidebar (navy)
# ---------------------------------------------------------------------------

SIDEBAR_BG_TOP      = "#14224A"
SIDEBAR_BG_BOTTOM   = "#0A162E"
SIDEBAR_TEXT        = "#F1F5F9"
SIDEBAR_TEXT_MUTED  = "#A8B6CC"
SIDEBAR_TEXT_DIM    = "#7C8BA6"  # placeholder removed below
SIDEBAR_ACCENT      = TEAL
SIDEBAR_ACCENT_BG   = "rgba(20,184,166,0.14)"
SIDEBAR_BORDER      = "rgba(255,255,255,0.07)"
SIDEBAR_MUTED       = "#8DA0BF"


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

INFO           = NAVY
INFO_BG        = "#EEF1F8"


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
RADIUS_LG = "12px"

SHADOW_SM = (
    "0 1px 2px rgba(16,32,61,0.05), "
    "0 1px 1px rgba(16,32,61,0.03)"
)
SHADOW_MD = "0 4px 16px rgba(16,32,61,0.08)"
SHADOW_LG = "0 8px 24px rgba(16,32,61,0.12)"


# ---------------------------------------------------------------------------
# Confidence colors
# ---------------------------------------------------------------------------

CONFIDENCE_COLORS = {
    "High":   (SUCCESS, SUCCESS_BG),
    "Medium": (WARNING, WARNING_BG),
    "Low":    (DANGER, DANGER_BG),
}

CONFIDENCE_LEGEND = "≥0.8 High · 0.5–0.8 Medium · <0.5 Low"


# ---------------------------------------------------------------------------
# Apply global theme
# ---------------------------------------------------------------------------

def apply_theme():

    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link
            href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap"
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
            padding-top: 1.25rem !important;
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
            background: {BG} !important;
        }}

        /* =====================================================
           ALERTS
        ===================================================== */

        div[data-testid="stAlert"] {{
            border-radius: 8px !important;
            border: none !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        }}

        div[data-testid="stAlertContainer"][kind="info"] {{
            background: #EEF1F8 !important;
            border-left: 3px solid {NAVY} !important;
            color: #1A2B4A !important;
        }}

        div[data-testid="stAlertContainer"][kind="warning"] {{
            background: #FFFBEB !important;
            border-left: 3px solid #F59E0B !important;
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

        /* Streamlit renders expander/status header icons (chevron, state icon)
           as Material Symbols ligature spans. The status state icon uses the
           stExpanderIcon* testids, NOT stIconMaterial — so without this rule
           the blanket `.stApp span` Inter override makes the raw ligature text
           ("check", "keyboard_arrow_down", ...) leak next to labels such as
           "Show full answer" / "Report complete" (untouched labels). */
        [data-testid="stIconMaterial"],
        [data-testid^="stExpanderIcon"] {{
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
            font-size: 30px !important;
            font-weight: 600 !important;
            letter-spacing: -0.015em;
            font-family: 'Fraunces', Georgia, 'Times New Roman', serif !important;
            color: {PRIMARY} !important;
            line-height: 1.15;
            margin-top: 0 !important;
            margin-bottom: 4px !important;
        }}

        h2, h3 {{
            color: {TEXT_PRIMARY};
            font-weight: 600 !important;
            letter-spacing: -0.01em;
            font-family: 'Fraunces', Georgia, 'Times New Roman', serif !important;
        }}

        h2 {{ font-size: 22px !important; }}
        h3 {{ font-size: 18px !important; }}

        .subtle-caption {{
            color: {TEXT_TERTIARY};
            font-size: 12px;
        }}

        h5, .ia-section-h {{
            font-size: 16px !important;
            font-weight: 600 !important;
            color: {PRIMARY} !important;
            margin-bottom: 10px !important;
            letter-spacing: -0.005em;
            font-family: 'Inter', sans-serif !important;
        }}

        .page-sub {{
            color: {TEXT_TERTIARY};
            font-size: 14px;
            margin-top: -6px;
            margin-bottom: 18px;
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
            border-left: 3px solid {TEAL} !important;
            border-radius: 10px !important;
            box-shadow: {SHADOW_SM} !important;
            padding: 16px 16px !important;
        }}

        div[data-testid="stMetric"]:hover {{
            box-shadow: {SHADOW_MD} !important;
            border-color: {BORDER_HOVER} !important;
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
           CARDS (neutral, teal reserved for highlights)
        ===================================================== */

        div[data-testid="stVerticalBlockBorderWrapper"] > div {{
            background: #FFFFFF !important;
            border-radius: 10px !important;
            border: 1px solid {BORDER} !important;
            box-shadow: {SHADOW_SM} !important;
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid {BORDER} !important;
            border-radius: 10px !important;
            background: {BG} !important;
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
            background: {PRIMARY_HOVER} !important;
            border-color: {TEAL} !important;
            transform: translateY(-1px);
        }}

        .stButton button[kind="primary"] {{
            background: {PRIMARY} !important;
            border: 1px solid {PRIMARY} !important;
            box-shadow: 0 4px 14px rgba(16, 32, 61, 0.18) !important;
            color: white !important;
        }}

        .stButton button[kind="primary"]:hover {{
            background: {PRIMARY_HOVER} !important;
            border: 1px solid {TEAL} !important;
            box-shadow: 0 0 0 3px {TEAL_SOFT}, 0 6px 16px rgba(16,32,61,0.16) !important;
        }}

        div[data-testid="stTextInput"] input {{
            border-radius: 8px !important;
            border: 1.5px solid {BORDER_HOVER} !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        }}

        div[data-testid="stTextInput"] input:focus {{
            border-color: {TEAL} !important;
            box-shadow: 0 0 0 3px {TEAL_SOFT} !important;
        }}


        /* =====================================================
           CHAT INPUT  (query composer)
        ===================================================== */

        div[data-testid="stChatInput"] {{
            background: #FFFFFF !important;
            border: 1.5px solid {BORDER_HOVER} !important;
            border-radius: 14px !important;
            box-shadow: 0 2px 8px rgba(16,32,61,0.06) !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        }}

        div[data-testid="stChatInput"]:focus-within {{
            border-color: {TEAL} !important;
            box-shadow: 0 0 0 3px {TEAL_SOFT}, 0 6px 18px rgba(16,32,61,0.08) !important;
        }}

        div[data-testid="stChatInput"] * {{
            outline: none !important;
        }}

        div[data-testid="stChatInput"] textarea {{
            padding: 13px 8px 13px 16px !important;
            min-height: 50px !important;
            line-height: 1.5 !important;
        }}

        div[data-testid="stChatInput"] button {{
            border-radius: 10px !important;
            margin-right: 6px !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease !important;
        }}

        div[data-testid="stChatInput"] button:hover {{
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 14px {TEAL_SOFT} !important;
        }}

        div[data-testid="stChatInput"] button:active {{
            transform: translateY(0) !important;
        }}


        /* =====================================================
           CHAT MESSAGES
        ===================================================== */

        .insight-card,
        .ai-answer-card {{
            background: #FFFFFF !important;
            border: 1px solid {BORDER} !important;
            border-left: 3px solid {TEAL} !important;
            border-radius: 10px !important;
            padding: 18px 22px !important;
            box-shadow: {SHADOW_SM} !important;
        }}

        .ai-answer-card {{
            margin-bottom: 6px !important;
        }}

        div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"])
        [data-testid="stChatMessageContent"] {{
            background: #F4F6FA !important;
            border: 1px solid {BORDER} !important;
            border-left: 3px solid {TEAL} !important;
            border-radius: 10px !important;
            padding: 18px 22px !important;
            box-shadow: {SHADOW_SM} !important;
            max-width: 100% !important;
        }}

        div[data-testid="stChatMessage"] {{
            width: 100% !important;
            margin-bottom: 12px !important;
        }}

        div[data-testid="stChatMessageContent"],
        .ai-answer-card {{
            overflow-wrap: break-word;
        }}

        div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
            display: flex !important;
            flex-direction: row-reverse !important;
            justify-content: flex-start !important;
            gap: 8px !important;
        }}

        div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
        [data-testid="stChatMessageContent"] {{
            background: #F4F6FA !important;
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
            background: #F4F6FA !important;
            border: 1px solid {BORDER} !important;
            border-radius: 999px !important;
            padding: 4px 12px !important;
            font-size: 12px !important;
            font-weight: 500 !important;
            color: {TEXT_SECONDARY} !important;
            min-height: 28px !important;
        }}

        div[class*="st-key-conf_chip_high"] div[data-testid="stPopover"] > button {{
            background: {SUCCESS_BG} !important;
            border: 1px solid #C6F6D5 !important;
            border-radius: 6px !important;
            box-shadow: none !important;
            font-weight: 500 !important;
            color: #047857 !important;
        }}

        div[class*="st-key-conf_chip_medium"] div[data-testid="stPopover"] > button {{
            background: {WARNING_BG} !important;
            border: 1px solid #FDE68A !important;
            border-radius: 6px !important;
            box-shadow: none !important;
            font-weight: 500 !important;
            color: #B45309 !important;
        }}

        div[class*="st-key-conf_chip_low"] div[data-testid="stPopover"] > button {{
            background: {DANGER_BG} !important;
            border: 1px solid #FECACA !important;
            border-radius: 6px !important;
            box-shadow: none !important;
            font-weight: 500 !important;
            color: #B91C1C !important;
        }}

        div[class*="st-key-conf_chip"] div[data-testid="stPopover"] > button p {{
            color: inherit !important;
            font-size: 12px !important;
        }}


        /* =====================================================
           SIDEBAR BASE
        ===================================================== */

        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {SIDEBAR_BG_TOP} 0%, {SIDEBAR_BG_BOTTOM} 100%) !important;
            border-right: 1px solid {SIDEBAR_BORDER} !important;
            min-width: 264px !important;
            max-width: 264px !important;
            width: 264px !important;
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
            border-color: {SIDEBAR_BORDER} !important;
            margin: {SPACE_4} 0;
        }}


        /* =====================================================
           PAGE NAVIGATION
        ===================================================== */

        section[data-testid="stSidebarNav"] {{
            display: block !important;
            padding-top: 0 !important;
            margin-bottom: 8px !important;
        }}

        section[data-testid="stSidebarNav"] a {{
            color: {SIDEBAR_TEXT_MUTED} !important;
            border-radius: 7px !important;
            padding: 8px 12px !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            margin: 1.5px 0 !important;
            transition: background 0.15s ease, color 0.15s ease, transform 0.15s ease !important;
        }}

        section[data-testid="stSidebarNav"] a:hover {{
            background: rgba(255,255,255,0.05) !important;
            color: #E2E8F0 !important;
            transform: translateX(2px) !important;
        }}

        section[data-testid="stSidebarNav"] a [data-testid="stNavPageIcon"] {{
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            vertical-align: middle !important;
            margin-right: 8px !important;
            line-height: 0 !important;
        }}

        /* Icons are shown for EVERY nav item at all times - the active item is
           distinguished by background/color, never by icon presence. */
        section[data-testid="stSidebarNav"] a [data-testid="stNavPageIcon"] {{
            display: inline-flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            color: {SIDEBAR_TEXT_MUTED} !important;
        }}

        section[data-testid="stSidebarNav"] a[aria-current="page"] [data-testid="stNavPageIcon"],
        section[data-testid="stSidebarNav"] [aria-current="page"] [data-testid="stNavPageIcon"] {{
            color: #FFFFFF !important;
        }}

        section[data-testid="stSidebarNav"] a[aria-current="page"],
        section[data-testid="stSidebarNav"] [aria-current="page"],
        section[data-testid="stSidebar"] [aria-current="page"] {{
            background: {SIDEBAR_ACCENT_BG} !important;
            color: #FFFFFF !important;
            box-shadow: inset 3px 0 0 {SIDEBAR_ACCENT} !important;
            font-weight: 600 !important;
            border-radius: 7px !important;
        }}

        .ia-nav-label {{
            font-size: 10px !important;
            font-weight: 600 !important;
            letter-spacing: 0.12em !important;
            text-transform: uppercase !important;
            color: {SIDEBAR_TEXT_DIM} !important;
            margin: 16px 4px 6px 4px !important;
        }}

        .ia-nav-label:first-child {{
            margin-top: 8px !important;
        }}


        /* =====================================================
           BRAND
        ===================================================== */

        .ia-brand {{
            padding: 6px 4px 14px 4px !important;
            margin-bottom: 6px !important;
        }}

        .ia-brand-title {{
            font-size: 19px !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
            color: {SIDEBAR_TEXT} !important;
            line-height: 1.2 !important;
            display: flex;
            align-items: center;
        }}

        .ia-brand-title span {{
            color: {SIDEBAR_ACCENT} !important;
        }}

        .ia-brand-mark svg {{
            width: 26px;
            height: 26px;
            margin-right: 8px;
        }}

        .ia-brand-subtitle {{
            margin-top: 3px !important;
            font-size: 10px !important;
            font-weight: 600 !important;
            color: {SIDEBAR_TEXT_DIM} !important;
            letter-spacing: 0.10em !important;
            text-transform: uppercase !important;
        }}


        /* =====================================================
           CHAT HERO (compact)
        ===================================================== */

        .ia-hero {{
            text-align: center;
            animation: iaHeroFade 0.4s ease both;
            margin: 2vh auto 0 auto !important;
            padding: 0 !important;
            max-width: 720px;
        }}

        .ia-logo {{
            line-height: 0;
            text-align: center;
        }}

        .ia-logo svg {{
            height: 72px;
            width: auto;
            max-width: 100%;
            display: inline-block;
            transition: opacity 0.2s ease;
            opacity: 0.99;
        }}

        .ia-hero-name {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: {PRIMARY};
            margin: 8px 0 0 0;
            line-height: 1.15;
        }}

        .ia-hero-name span {{
            color: {TEAL};
        }}

        .ia-hero-sub {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 13.5px;
            font-weight: 500;
            letter-spacing: 0.01em;
            color: {TEXT_SECONDARY};
            margin: 2px 0 0 0;
            line-height: 1.4;
        }}

        .ia-hero-desc {{
            font-size: 12.5px;
            font-weight: 400;
            color: {TEXT_TERTIARY};
            max-width: 520px;
            margin: 4px auto 0 auto;
            line-height: 1.5;
        }}

        .ia-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 8px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.04em;
            color: {TEAL};
            background: {TEAL_SOFT};
            border: 1px solid rgba(20,184,166,0.28);
            border-radius: 999px;
            padding: 3px 12px;
        }}

        .ia-badge::before {{
            content: "";
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: {TEAL};
            flex: 0 0 auto;
        }}

        .ia-hero--compact {{
            text-align: left;
            margin: 0 0 2px 0 !important;
            padding: 0 0 2px 0 !important;
        }}

        .ia-hero--compact .ia-logo {{
            display: inline-flex;
            vertical-align: middle;
            width: auto;
            margin-right: 10px;
        }}

        .ia-hero--compact .ia-logo svg {{
            height: 34px;
        }}

        .ia-hero--compact .ia-hero-name {{
            display: inline-flex;
            vertical-align: middle;
            font-size: 19px;
            margin: 0;
        }}

        .ia-hero--compact .ia-hero-sub {{
            font-size: 12px;
            margin: 4px 0 0 0;
        }}

        .ia-hero--compact .ia-badge {{
            margin-top: 6px;
            font-size: 10.5px;
            padding: 3px 10px;
        }}

        @keyframes iaHeroFade {{
            from {{ opacity: 0; transform: translateY(4px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}

        @media (max-width: 768px) {{
            .ia-logo svg {{ height: 38px; }}
            .ia-hero-name {{ font-size: 21px; }}
        }}


        /* =====================================================
           PRE-AUTH LANDING / AUTH VIEWS (entry experience)
        ===================================================== */

        .landing-nav {{
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .landing-nav-divider {{
            border: none;
            border-top: 1px solid {BORDER};
            margin: 14px 0 0 0;
        }}

        .landing-hero {{
            text-align: center;
            margin: 7vh auto 0 auto !important;
            max-width: 760px;
            animation: iaHeroFade 0.4s ease both;
        }}

        .landing-title {{
            font-family: 'Fraunces', Georgia, 'Times New Roman', serif !important;
            font-size: 52px !important;
            font-weight: 600 !important;
            letter-spacing: -0.03em !important;
            color: {PRIMARY} !important;
            line-height: 1.05;
            margin: 0 !important;
        }}

        .landing-title span {{
            color: {TEAL} !important;
        }}

        .landing-tagline {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 15.5px;
            font-weight: 400;
            color: {TEXT_SECONDARY};
            max-width: 560px;
            margin: 14px auto 0 auto;
            line-height: 1.6;
        }}

        .landing-cta-gap {{
            height: 26px;
        }}

        /* Nav "Sign in" = outline, not filled */
        [class*="st-key-landing_signin_btn"] .stButton button,
        [class*="st-key-landing_signin_btn"] button {{
            background: transparent !important;
            border: 1px solid {BORDER_HOVER} !important;
            color: {TEXT_SECONDARY} !important;
            box-shadow: none !important;
            font-weight: 600 !important;
            height: 36px !important;
        }}
        [class*="st-key-landing_signin_btn"] button:hover {{
            border-color: {PRIMARY} !important;
            color: {PRIMARY} !important;
            background: transparent !important;
            transform: none !important;
        }}

        /* Hero primary CTA = filled teal */
        [class*="st-key-landing_demo_btn"] .stButton button,
        [class*="st-key-landing_demo_btn"] button {{
            background: {TEAL} !important;
            border: 1px solid {TEAL} !important;
            color: #FFFFFF !important;
            box-shadow: 0 8px 20px rgba(20, 184, 166, 0.28) !important;
            font-weight: 700 !important;
            font-size: 15px !important;
            height: 44px !important;
        }}
        [class*="st-key-landing_demo_btn"] button:hover {{
            background: #0EA5A0 !important;
            border-color: #0EA5A0 !important;
            box-shadow: 0 10px 24px rgba(20, 184, 166, 0.30) !important;
            transform: translateY(-1px) !important;
        }}

        /* Hero "Sign in" link = text link, no button chrome */
        [class*="st-key-hero_signin_btn"] .stButton button,
        [class*="st-key-hero_signin_btn"] button {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #0F766E !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            height: auto !important;
        }}
        [class*="st-key-hero_signin_btn"] button:hover {{
            color: {PRIMARY} !important;
            text-decoration: underline !important;
            background: transparent !important;
            transform: none !important;
        }}

        /* Auth view "Back" = outline */
        [class*="st-key-auth_back_btn"] .stButton button,
        [class*="st-key-auth_back_btn"] button {{
            background: transparent !important;
            border: 1px solid {BORDER_HOVER} !important;
            color: {TEXT_SECONDARY} !important;
            box-shadow: none !important;
            font-weight: 600 !important;
            height: 36px !important;
        }}
        [class*="st-key-auth_back_btn"] button:hover {{
            border-color: {PRIMARY} !important;
            color: {PRIMARY} !important;
            background: transparent !important;
            transform: none !important;
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
           MODE SWITCHER
        ===================================================== */

        section[data-testid="stSidebar"] div[role="radiogroup"] {{
            background: rgba(255,255,255,0.05) !important;
            border-radius: 10px !important;
            padding: 4px !important;
            border: 1px solid {SIDEBAR_BORDER} !important;
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
            border-radius: 8px !important;
            padding: 8px 10px !important;
            font-size: 12.5px !important;
            font-weight: 500 !important;
            color: {SIDEBAR_TEXT_MUTED} !important;
        }}

        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
            background: {TEAL} !important;
            color: {NAVY} !important;
            font-weight: 600 !important;
            box-shadow: 0 0 14px {TEAL_SOFT} !important;
        }}

        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked),
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) * {{
            color: {NAVY} !important;
        }}

        section[data-testid="stSidebar"] div[role="radiogroup"] label:not(:has(input:checked)):hover {{
            background: rgba(255,255,255,0.04) !important;
            color: #E2E8F0 !important;
        }}

        /* Sidebar nav + page-header icons must stay clearly visible on the dark
           navy background. Streamlit paints nav FontIcon spans with the light-
           theme text color inline; force them light (white when active/hovered). */
        section[data-testid="stSidebar"] [data-testid="stIconMaterial"] {{
            color: #CBD5E1 !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover [data-testid="stIconMaterial"],
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] [data-testid="stIconMaterial"] {{
            color: #FFFFFF !important;
        }}


        /* =====================================================
           SIDEBAR HISTORY ROWS
        ===================================================== */

        .ia-history-empty {{
            background: rgba(255,255,255,0.04);
            border: 1px dashed rgba(255,255,255,0.14);
            border-radius: {RADIUS_MD};
            padding: {SPACE_4};
            text-align: center;
            margin: 4px 2px;
        }}

        .ia-empty-title {{
            color: {SIDEBAR_TEXT};
            font-size: 13px;
            font-weight: 600;
            margin: 0;
        }}

        .ia-empty-text {{
            color: {SIDEBAR_TEXT_DIM};
            font-size: 12px;
            margin-top: 3px;
            line-height: 1.4;
        }}

        div[class*="st-key-history_row"] {{
            border-radius: 7px !important;
            margin: 2px 2px !important;
            transition: background 0.15s ease, box-shadow 0.15s ease !important;
        }}

        div[class*="st-key-history_row"]:hover {{
            background: rgba(255,255,255,0.05) !important;
        }}

        div[class*="st-key-history_row_active"] {{
            background: {SIDEBAR_ACCENT_BG} !important;
            box-shadow: inset 3px 0 0 {SIDEBAR_ACCENT} !important;
            border-radius: 7px !important;
        }}

        div[class*="st-key-history_row_active"]:hover {{
            background: {SIDEBAR_ACCENT_BG} !important;
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
            padding: 9px 12px !important;
            width: 100% !important;
            border-radius: 6px !important;
            transition: color 0.15s ease !important;
        }}

        div[class*="st-key-history_row"] button:hover {{
            color: {SIDEBAR_TEXT} !important;
        }}

        div[class*="st-key-history_row_active"] button {{
            color: #FFFFFF !important;
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
            background: {TEAL} !important;
            border: 1px solid {TEAL} !important;
            border-radius: 6px !important;
            color: {NAVY} !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 10px rgba(20,184,166,0.25) !important;
        }}

        section[data-testid="stSidebar"] button[kind="primary"] p {{
            color: {NAVY} !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            margin: 0 !important;
        }}

        section[data-testid="stSidebar"] button[kind="primary"]:hover {{
            background: #2DD4BF !important;
            border: 1px solid #2DD4BF !important;
            box-shadow: 0 0 0 3px {TEAL_SOFT} !important;
        }}


        /* =====================================================
           SUGGESTED ANALYSIS CARDS
        ===================================================== */

        .ia-subhead {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 18px;
            font-weight: 600;
            letter-spacing: -0.01em;
            color: {PRIMARY};
            text-align: center;
            margin: 18px 0 4px 0;
            line-height: 1.25;
        }}

        .ia-suggestion-label {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: {TEXT_TERTIARY};
            text-align: center;
            margin: 22px 0 10px 0;
        }}

        div[class*="st-key-sugg_"] .stButton button {{
            background: #FFFFFF !important;
            border: 1px solid {BORDER} !important;
            border-radius: 12px !important;
            box-shadow: {SHADOW_SM} !important;
            color: {TEXT_SECONDARY} !important;
            font-size: 13px !important;
            font-weight: 400 !important;
            padding: 14px 16px !important;
            min-height: 92px !important;
            white-space: normal !important;
            line-height: 1.45 !important;
            height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: flex-start !important;
            justify-content: center !important;
            gap: 4px !important;
            text-align: left !important;
            transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease !important;
        }}

        div[class*="st-key-sugg_"] .stButton button [data-testid="stBaseButton-label"] {{
            justify-content: flex-start !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: flex-start !important;
            text-align: left !important;
            padding: 0 !important;
            margin: 0 !important;
        }}

        div[class*="st-key-sugg_"] .stButton button p {{
            margin: 0 !important;
            text-align: left !important;
            color: {TEXT_SECONDARY} !important;
            font-size: 13px !important;
            white-space: pre-line !important;
            line-height: 1.45 !important;
            display: block !important;
        }}

        div[class*="st-key-sugg_"] .stButton button p::first-line {{
            color: {PRIMARY} !important;
            font-weight: 600 !important;
            font-size: 14px !important;
        }}

        div[class*="st-key-sugg_"] .stButton button:hover {{
            border-color: #BFD5E6 !important;
            box-shadow: {SHADOW_MD} !important;
            transform: translateY(-1px) !important;
        }}

        /* Keep suggestion-card icons teal and small */
        div[class*="st-key-sugg_"] .stButton button [data-testid="stBaseButton-icon"] svg {{
            color: {TEAL} !important;
            width: 15px !important;
            height: 15px !important;
        }}

        div[class*="st-key-sugg_"] .stButton button [data-testid="stBaseButton-icon"] {{
            color: {TEAL} !important;
            font-size: 16px !important;
            margin-right: 0 !important;
            margin-bottom: 2px !important;
        }}


        /* =====================================================
           ACCESSIBILITY
        ===================================================== */

        button:focus-visible,
        a:focus-visible,
        input:focus-visible,
        textarea:focus-visible,
        select:focus-visible,
        [data-testid="stBaseButton"]:focus-visible,
        [data-testid="stChatInput"] *:focus-visible {{
            outline: 2px solid {TEAL} !important;
            outline-offset: 2px !important;
            box-shadow: 0 0 0 3px {TEAL_SOFT} !important;
        }}


        /* =====================================================
           CHIP ROW (wrap on narrow screens)
        ===================================================== */

        div[class*="st-key-chip_row"] {{
            display: flex !important;
            flex-wrap: wrap;
            gap: 6px;
        }}

        div[class*="st-key-chip_row"] [data-testid="stColumn"] {{
            flex: 0 0 auto !important;
            width: auto !important;
        }}


        /* =====================================================
           EMPTY STATE
        ===================================================== */

        .ia-empty-state {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 28px 20px;
            text-align: center;
            color: {TEXT_SECONDARY};
            font-size: 14px;
            line-height: 1.5;
            margin-top: 6px;
        }}


        /* =====================================================
           REDUCED MOTION
        ===================================================== */

        @media (prefers-reduced-motion: reduce) {{
            *,
            *::before,
            *::after {{
                animation: none !important;
                transition: none !important;
                transform: none !important;
            }}
        }}

        /* =====================================================
           PROCESSING STEP INDICATOR (Chat page st.status body)
        ===================================================== */

        .ia-steps {{
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin: 2px 0 0;
        }}

        .ia-step {{
            display: flex;
            align-items: center;
            gap: 9px;
            font-size: 13.5px;
            line-height: 1.35;
        }}

        .ia-step-icon {{
            width: 17px;
            height: 17px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex: 0 0 auto;
        }}

        .ia-step-icon.done {{
            color: #14B8A6;
            font-weight: 700;
            font-size: 13px;
        }}

        .ia-step.active .ia-step-text {{
            color: #10203D;
            font-weight: 600;
        }}

        .ia-step.done .ia-step-text {{
            color: #94A3B8;
        }}

        .ia-step.pending .ia-step-text {{
            color: #B6BECB;
        }}

        .ia-spinner {{
            width: 13px;
            height: 13px;
            border: 2px solid #D3DBE5;
            border-top-color: #14B8A6;
            border-radius: 50%;
            display: inline-block;
            animation: ia-spin 0.8s linear infinite;
        }}

        @keyframes ia-spin {{
            to {{
                transform: rotate(360deg);
            }}
        }}

        /* =====================================================
           PERSISTED "ANALYSIS COMPLETE" SUMMARY (Chat messages)
           Collapsed-by-default chrome-less toggle holding the
           finished step checklist so it never vanishes after the
           rerun that swaps the live st.status for the answer card.
        ===================================================== */

        div[class*="st-key-proc_"] [data-testid="stExpander"] {{
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
            border-radius: 0 !important;
            padding: 0 !important;
            margin: 0 0 2px !important;
        }}
        div[class*="st-key-proc_"] [data-testid="stExpander"] summary {{
            color: #0F766E !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            padding: 4px 0 4px 2px !important;
            min-height: 0 !important;
            background: transparent !important;
            cursor: pointer !important;
            letter-spacing: 0.1px !important;
        }}
        div[class*="st-key-proc_"] [data-testid="stExpander"] summary [data-testid="stIconMaterial"] {{
            color: #0F766E !important;
            font-size: 15px !important;
        }}
        div[class*="st-key-proc_"] [data-testid="stExpanderDetails"] {{
            border-left: 2px solid #CCF5F0 !important;
            padding: 8px 0 2px 12px !important;
            margin: 2px 0 0 2px !important;
        }}
        div[class*="st-key-proc_"] .ia-steps {{
            gap: 5px;
            margin: 0;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )

    # Fallback JS for user message alignment and sidebar brand
    st.markdown(
        """
<script>
function forceAlignUserMessages(doc) {
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
                content.style.setProperty('background', 'rgba(20,184,166,0.10)', 'important');
                content.style.setProperty('border', '1px solid rgba(20,184,166,0.30)', 'important');
                content.style.setProperty('border-radius', '16px 16px 4px 16px', 'important');
                content.style.setProperty('padding', '12px 16px', 'important');
                content.style.setProperty('max-width', '70%', 'important');
                content.style.setProperty('margin-left', 'auto', 'important');
            }
        }
    });
}

function addSidebarSectionLabels(doc) {
    const content = doc.querySelector('[data-testid="stSidebarContent"]');
    if (!content) return;
    const nav = doc.querySelector('[data-testid="stSidebarNav"]');
    if (nav && !content.querySelector('.ia-brand-nav-label')) {
        const lab = doc.createElement('div');
        lab.className = 'ia-nav-label ia-brand-nav-label';
        lab.textContent = 'MAIN';
        content.insertBefore(lab, nav);
    }
    if (nav && !content.querySelector('.ia-analysis-nav-label')) {
        const anchors = Array.from(nav.querySelectorAll('a'));
        const historyAnchor = anchors.find(
            a => (a.textContent || '').trim().toLowerCase().includes('history')
        );
        if (historyAnchor) {
            const lab2 = doc.createElement('div');
            lab2.className = 'ia-nav-label ia-analysis-nav-label';
            lab2.textContent = 'ANALYSIS';
            nav.insertBefore(lab2, historyAnchor);
        }
    }
}

function attachCritiqueTooltips(doc) {
    var CONFIDENCE_HELP = 'Confidence scale: \u22650.8 High \u00B7 0.5\u20130.8 Medium \u00B7 <0.5 Low';
    var CRITIQUE_HELP = 'An internal review step that checks the answer against source data before it is returned to you.';
    const nodes = doc.querySelectorAll('[data-testid="stPopover"] > button');
    nodes.forEach(btn => {
        const txt = (btn.textContent || '').trim();
        const lower = txt.toLowerCase();
        if (lower.indexOf('critique:') === 0) {
            btn.setAttribute('title', CRITIQUE_HELP);
        } else if (/(high|medium|low)\s*\u00B7/.test(lower)) {
            btn.setAttribute('title', CONFIDENCE_HELP);
        }
    });
}

function watchDoc(doc) {
    if (!doc || doc.__iaWatched) return;
    doc.__iaWatched = true;
    const apply = () => {
        forceAlignUserMessages(doc);
        addSidebarSectionLabels(doc);
        attachCritiqueTooltips(doc);
    };
    if (doc.readyState === 'loading') {
        doc.addEventListener('DOMContentLoaded', apply);
    } else {
        apply();
    }
    const observer = new MutationObserver(apply);
    observer.observe(doc.body, { childList: true, subtree: true });
}

watchDoc(document);
watchDoc(window.parent.document);
</script>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------

def spacer(size: str = "md"):
    st.markdown(f'<div class="spacer-{size}"></div>', unsafe_allow_html=True)


def section_label(text: str):
    st.markdown(f'<div class="sb-label">{html.escape(text)}</div>', unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    st.title(title)
    if subtitle:
        st.markdown(
            f'<p class="page-sub">{html.escape(subtitle)}</p>',
            unsafe_allow_html=True,
        )


def section_header(text: str):
    st.markdown(
        f'<div class="ia-section-label" style="color:{TEXT_TERTIARY}">{html.escape(text)}</div>',
        unsafe_allow_html=True,
    )


def render_sidebar_brand():
    st.markdown(
        """
        <div class="ia-brand">
            <div class="ia-brand-title">
                <span class="ia-brand-mark" aria-hidden="true">
                    <svg width="26" height="26" viewBox="0 0 96 96" fill="none">
                        <rect x="6" y="6" width="84" height="84" rx="20" fill="#10203D"/>
                        <path d="M24 64 L44 46 L56 54 L70 36" stroke="#FFFFFF" stroke-width="8"
                            stroke-linecap="round" stroke-linejoin="round"/>
                        <circle cx="70" cy="36" r="7" fill="#14B8A6"/>
                    </svg>
                </span> Insight<span>AI</span>
            </div>
            <div class="ia-brand-subtitle">Business Intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


_LOGO_SVG_CACHE = None


def app_logo_svg() -> str:
    """Return the application logo (logo/logo.svg) as inline SVG markup."""
    global _LOGO_SVG_CACHE
    if _LOGO_SVG_CACHE is None:
        logo_path = pathlib.Path(__file__).resolve().parent.parent / "logo" / "logo.svg"
        try:
            _LOGO_SVG_CACHE = logo_path.read_text(encoding="utf-8")
        except OSError:
            _LOGO_SVG_CACHE = ""
    return _LOGO_SVG_CACHE


_FAVICON_SVG_CACHE = None


def favicon_mark_svg() -> str:
    """Return the favicon mark (logo/favicon.svg) as raw inline SVG markup.

    Single source of truth for the small brand icon: every in-page header
    lockup and the browser-tab favicon share this exact art.
    """
    global _FAVICON_SVG_CACHE
    if _FAVICON_SVG_CACHE is None:
        favicon_path = pathlib.Path(__file__).resolve().parent.parent / "logo" / "favicon.svg"
        try:
            _FAVICON_SVG_CACHE = favicon_path.read_text(encoding="utf-8")
        except OSError:
            _FAVICON_SVG_CACHE = ""
    return _FAVICON_SVG_CACHE


# ---------------------------------------------------------------------------
# Chips / badges
# ---------------------------------------------------------------------------

def confidence_badge_html(label: str, score: float) -> str:
    label = html.escape(str(label))
    score_txt = f"{score:.2f}"
    if label == "High":
        bg, fg, bd = SUCCESS_BG, "#047857", "#A7F3D0"
    elif label == "Medium":
        bg, fg, bd = WARNING_BG, "#B45309", "#FDE68A"
    else:
        bg, fg, bd = DANGER_BG, "#B91C1C", "#FECACA"
    return (
        f'<span style="font-size:11px;font-weight:500;padding:3px 10px;'
        f'border-radius:6px;background:{bg};color:{fg};border:1px solid {bd};'
        f'font-family:\'IBM Plex Mono\',monospace;">'
        f'{label} · {score_txt}</span>'
    )


def confidence_legend() -> str:
    """HTML 'ⓘ' carrying the confidence scale as a native hover tooltip.

    Reusable everywhere confidence is shown (chat, dashboard, history) so the
    thresholds can never drift between pages: "≥0.8 High · 0.5–0.8 Medium · <0.5 Low".
    """
    return (
        f'<span title="{html.escape(CONFIDENCE_LEGEND)}" '
        f'style="cursor:help;margin-left:5px;font-size:11.5px;'
        f'color:{TEXT_TERTIARY};">ⓘ</span>'
    )


_STATUS_BADGES = {
    "neutral": ("#F4F6FA", TEXT_SECONDARY),
    "success": (SUCCESS_BG, "#047857"),
    "warning": (WARNING_BG, "#B45309"),
    "danger":  (DANGER_BG, "#B91C1C"),
    "info":    (INFO_BG, NAVY),
    "teal":    ("#E6FBFA", TEAL),
}


def status_badge(label: str, tone: str = "neutral"):
    bg, fg = _STATUS_BADGES.get(tone, _STATUS_BADGES["neutral"])
    return (
        f'<span style="font-size:11px;font-weight:600;padding:3px 10px;'
        f'border-radius:999px;background:{bg};color:{fg};display:inline-block;'
        f'margin-right:6px;">{html.escape(str(label))}</span>'
    )


def source_tag_html(label: str) -> str:
    return (
        f'<span style="font-size:11px;color:{TEXT_SECONDARY};background:#F4F6FA;'
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


# ---------------------------------------------------------------------------
# Cards / empty state
# ---------------------------------------------------------------------------

def empty_state(message: str):
    st.markdown(
        f'<div class="ia-empty-state">{message}</div>',
        unsafe_allow_html=True,
    )


def stat_card(label: str, value: str, delta: str = "", accent: str = TEAL):
    """Compact technical card (performance monitor)."""
    st.markdown(
        f"""
        <div style="
            background:#FFFFFF; border:1px solid {BORDER};
            border-top:3px solid {accent}; border-radius:12px;
            padding:14px 16px; box-shadow:{SHADOW_SM};
        ">
            <div style="font-size:11px; font-weight:600; color:{TEXT_SECONDARY}; letter-spacing:0.4px;
                text-transform:uppercase; margin-bottom:6px;">{label}</div>
            <div style="font-size:24px; font-weight:700; color:#0F172A; line-height:1.1;">{value}</div>
            <div style="font-size:12px; color:{TEXT_TERTIARY}; margin-top:5px;">{delta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, delta: str = "", accent: str = TEAL):
    """Larger KPI card for analytics highlights."""
    st.markdown(
        f"""
        <div style="
            background:#FFFFFF; border:1px solid {BORDER};
            border-left:3px solid {accent}; border-radius:12px;
            padding:18px 18px; box-shadow:0 1px 3px rgba(16,24,40,0.04);
        ">
            <div style="font-size:12px; font-weight:600; color:{TEXT_SECONDARY}; letter-spacing:0.4px;
                text-transform:uppercase; margin-bottom:10px;">{label}</div>
            <div style="font-size:26px; font-weight:700; color:{TEXT_PRIMARY}; line-height:1.1;
                font-family:'IBM Plex Mono',monospace;">{value}</div>
            <div style="font-size:12.5px; color:{TEXT_TERTIARY}; margin-top:6px;">{delta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def small_logo_html():
    mark = favicon_mark_svg().strip()
    if not mark:
        mark = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" '
            'viewBox="0 0 96 96" fill="none">'
            '<rect x="6" y="6" width="84" height="84" rx="20" fill="#10203D"/>'
            '<path d="M24 64 L44 46 L56 54 L70 36" stroke="#FFFFFF" '
            'stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>'
            '<circle cx="70" cy="36" r="7" fill="#14B8A6"/>'
            "</svg>"
        )
    else:
        mark = mark.replace("<svg ", '<svg style="width:34px;height:34px;" ', 1)
    span = (
        "<span style=\"font-family:'Inter',sans-serif; font-size:19px; "
        "font-weight:700; letter-spacing:-0.5px;\">"
        '<span style="color:#10203D;">Insight</span>'
        '<span style="color:#14B8A6;">AI</span>'
        "</span>"
    )
    return (
        '<div style="display:flex; align-items:center; gap:10px; margin-bottom: 8px;">'
        + mark
        + span
        + "</div>"
    )