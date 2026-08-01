"""
InsightAI - Shared theme, injected on every page.
Design direction: refined dark sidebar, light elevated canvas,
indigo accent, clean SaaS look.
"""

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
SIDEBAR_ACCENT      = "#818CF8"
SIDEBAR_ACCENT_BG   = "rgba(99,102,241,0.16)"
SIDEBAR_MUTED       = "#64748B"

BG                  = "#F7F8FA"
CARD_BG             = "#FFFFFF"
BORDER              = "#E8EAEE"
BORDER_HOVER        = "#D8DCE3"

PRIMARY             = "#4F46E5"
PRIMARY_HOVER       = "#4338CA"
PRIMARY_BG          = "#EEF2FF"
PRIMARY_SOFT        = "rgba(99,102,241,0.15)"

TEXT_PRIMARY        = "#111827"
TEXT_SECONDARY      = "#6B7280"
TEXT_TERTIARY       = "#9CA3AF"


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

INFO           = "#6366F1"
INFO_BG        = "#EEF2FF"


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
            padding-top: 0.6rem !important;
            padding-bottom: 3rem !important;
            height: auto !important;
            overflow: visible !important;
            max-width: 100% !important;
        }}

        [data-testid="stVerticalBlock"] {{
            height: auto !important;
            overflow: visible !important;
        }}

        .stApp {{
            background: linear-gradient(165deg, #F8FAFC 0%, #EEF2FF 55%, #E0E7FF 100%) !important;
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
            padding-top: 0.4rem !important;
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

        .mono-num {{
            font-family: 'JetBrains Mono', monospace !important;
            font-variant-numeric: tabular-nums;
        }}


        /* =====================================================
           TYPOGRAPHY
        ===================================================== */

        h1 {{
            font-size: 28px !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
            color: #0F172A !important;
        }}

        h2, h3 {{
            color: {TEXT_PRIMARY};
            font-weight: 600 !important;
            letter-spacing: -0.01em;
        }}

        .subtle-caption {{
            color: {TEXT_TERTIARY};
            font-size: 12px;
        }}

        div[data-testid="stMarkdown"] h5,
        .stMarkdown h5 {{
            font-size: 17px !important;
            font-weight: 600 !important;
            color: #1E293B !important;
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
            border: 1px solid #E0E7FF !important;
            border-left: 4px solid #6366F1 !important;
            border-radius: 14px !important;
            box-shadow: 0 2px 12px rgba(79, 70, 229, 0.08) !important;
            padding: 18px 16px !important;
        }}

        div[data-testid="stMetric"]:hover {{
            box-shadow: 0 6px 24px rgba(79,70,229,0.12) !important;
            border-color: #C7D2FE;
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
           CARDS
        ===================================================== */

        div[data-testid="stVerticalBlockBorderWrapper"] > div {{
            background: #FFFFFF !important;
            border-radius: 14px !important;
            border: 1px solid #E0E7FF !important;
            box-shadow: 0 2px 12px rgba(0,0,0,0.04) !important;
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid #E2E8F0 !important;
            border-radius: 10px !important;
            background: #F8FAFC !important;
        }}


        /* =====================================================
           BUTTONS / INPUTS
        ===================================================== */

        .stButton button {{
            border-radius: {RADIUS_MD};
            font-weight: 500;
        }}

        .stButton button[kind="primary"] {{
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%) !important;
            border: none !important;
            box-shadow: 0 4px 14px rgba(124, 58, 237, 0.35) !important;
            color: white !important;
        }}

        .stButton button[kind="primary"]:hover {{
            background: linear-gradient(135deg, {PRIMARY_HOVER} 0%, #6D28D9 100%);
            box-shadow: 0 0 16px rgba(124,58,237,0.35);
        }}

        div[data-testid="stTextInput"] input {{
            border-radius: {RADIUS_MD} !important;
            border: 1px solid {BORDER} !important;
        }}


        /* =====================================================
           CHAT INPUT
        ===================================================== */

        div[data-testid="stChatInput"] {{
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 14px !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.04) !important;
        }}

        div[data-testid="stChatInput"]:focus-within {{
            border-color: #6366F1 !important;
            box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
        }}

        div[data-testid="stChatInput"] * {{
            outline: none !important;
        }}


        /* =====================================================
           CHAT MESSAGES
        ===================================================== */

        .ai-answer-card {{
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 14px !important;
            padding: 16px 18px !important;
            box-shadow: 0 2px 12px rgba(0,0,0,0.04) !important;
            margin-bottom: 6px !important;
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
            border: 1px solid #E2E8F0 !important;
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
            box-shadow: 0 0 8px rgba(16,185,129,0.35) !important;
            font-weight: 600 !important;
            color: white !important;
        }}

        div[class*="st-key-conf_chip_medium"] div[data-testid="stPopover"] > button {{
            background: linear-gradient(90deg, #F59E0B, #FBBF24) !important;
            border: none !important;
            border-radius: 999px !important;
            font-weight: 600 !important;
            color: white !important;
        }}

        div[class*="st-key-conf_chip_low"] div[data-testid="stPopover"] > button {{
            background: linear-gradient(90deg, #EF4444, #F87171) !important;
            border: none !important;
            border-radius: 999px !important;
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
            color: #94A3B8 !important;
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
            background: rgba(99,102,241,0.16) !important;
            color: #E0E7FF !important;
            box-shadow: inset 3px 0 0 #818CF8 !important;
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
            color: #F8FAFC !important;
            line-height: 1.2 !important;
        }}

        .ia-brand-title span {{
            color: #A5B4FC !important;
        }}

        .ia-brand-mark {{
            color: #818CF8 !important;
            margin-right: 6px !important;
            font-size: 18px !important;
        }}

        .ia-brand-subtitle {{
            margin-top: 3px !important;
            font-size: 10px !important;
            font-weight: 600 !important;
            color: #94A3B8 !important;
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
            color: #64748B !important;
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
            color: #94A3B8 !important;
        }}

        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%) !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            box-shadow: 0 0 14px rgba(124,58,237,0.40) !important;
        }}

        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked),
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) * {{
            color: #FFFFFF !important;
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
            background: rgba(99,102,241,0.16) !important;
            box-shadow: inset 3px 0 0 #818CF8 !important;
            border-radius: 8px !important;
        }}

        div[class*="st-key-history_row"] button,
        div[class*="st-key-history_row"] [data-testid^="stBaseButton"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #CBD5E1 !important;
            text-align: left !important;
            font-size: 12.5px !important;
            font-weight: 500 !important;
            padding: 8px 12px !important;
            width: 100% !important;
            border-radius: 7px !important;
        }}

        div[class*="st-key-history_row_active"] button {{
            color: #F8FAFC !important;
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
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%) !important;
            border: none !important;
            border-radius: 10px !important;
            color: #FFFFFF !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.28) !important;
        }}

        section[data-testid="stSidebar"] button[kind="primary"] p {{
            color: #FFFFFF !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            margin: 0 !important;
        }}

        section[data-testid="stSidebar"] button[kind="primary"]:hover {{
            background: linear-gradient(135deg, #4338CA 0%, #6D28D9 100%) !important;
            box-shadow: 0 6px 16px rgba(79, 70, 229, 0.36) !important;
        }}


        /* =====================================================
           EXAMPLE QUESTION BUTTONS
        ===================================================== */

        div[data-testid="stHorizontalBlock"] .stButton button {{
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 12px !important;
            color: #334155 !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            padding: 14px 12px !important;
            min-height: 64px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
            white-space: normal !important;
            line-height: 1.35 !important;
        }}

        div[data-testid="stHorizontalBlock"] .stButton button:hover {{
            border-color: #C7D2FE !important;
            box-shadow: 0 4px 12px rgba(99,102,241,0.10) !important;
            color: #1E293B !important;
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
                            content.style.setProperty('border', '1px solid #E2E8F0', 'important');
                            content.style.setProperty('border-radius', '16px 16px 4px 16px', 'important');
                            content.style.setProperty('padding', '12px 16px', 'important');
                            content.style.setProperty('max-width', '70%', 'important');
                            content.style.setProperty('margin-left', 'auto', 'important');
                        }
                    }
                });
            });
        }

        forceAlignUserMessages();
        const observer = new MutationObserver(forceAlignUserMessages);
        observer.observe(window.parent.document.body, { childList: true, subtree: true });
        setInterval(forceAlignUserMessages, 1000);
        </script>
        """,
        unsafe_allow_html=True,
    )


def spacer(size: str = "md"):
    st.markdown(f'<div class="spacer-{size}"></div>', unsafe_allow_html=True)


def section_label(text: str):
    st.markdown(f'<div class="sb-label">{text}</div>', unsafe_allow_html=True)


def confidence_badge_html(label: str, score: float) -> str:
    if label == "High":
        return (
            f'<span style="font-size:11px;font-weight:600;padding:4px 12px;'
            f'border-radius:999px;background:linear-gradient(90deg,#10B981,#34D399);'
            f'color:white;box-shadow:0 0 8px rgba(16,185,129,0.35);">'
            f'{label} · {score:.2f}</span>'
        )
    elif label == "Medium":
        return (
            f'<span style="font-size:11px;font-weight:600;padding:4px 12px;'
            f'border-radius:999px;background:linear-gradient(90deg,#F59E0B,#FBBF24);'
            f'color:white;">'
            f'{label} · {score:.2f}</span>'
        )
    else:
        return (
            f'<span style="font-size:11px;font-weight:600;padding:4px 12px;'
            f'border-radius:999px;background:linear-gradient(90deg,#EF4444,#F87171);'
            f'color:white;">'
            f'{label} · {score:.2f}</span>'
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


def skeleton_loader():
    st.markdown(
        '<div class="skeleton-line" style="width:55%;"></div>'
        '<div class="skeleton-line" style="width:90%;"></div>'
        '<div class="skeleton-line" style="width:75%;"></div>',
        unsafe_allow_html=True,
    )