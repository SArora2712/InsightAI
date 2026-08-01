"""
InsightAI - History page (clean + 3-dot menu)
"""
import streamlit as st
from datetime import datetime

from core.theme2 import apply_theme
from core.history import (
    list_conversations,
    load_conversation_messages,
    delete_conversation,
    rename_conversation,
)

apply_theme()

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
st.markdown("""
<style>
.history-sub {
    color: #6B7280;
    font-size: 13.5px;
    margin-top: -4px;
    margin-bottom: 18px;
}

/* Search */
div[data-testid="stTextInput"] input {
    background: #FFFFFF !important;
    border: 1px solid #E8EAEE !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
}

.result-count {
    font-size: 12.5px;
    color: #9CA3AF;
    margin: 10px 0 14px 2px;
}

/* Card */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border: 1px solid #E8EAEE !important;
    border-radius: 14px !important;
    box-shadow: 0 1px 2px rgba(16,24,40,0.04) !important;
    padding: 4px 6px 1px 6px !important;
    margin-bottom: 2px !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #C7D2FE !important;
    box-shadow: 0 4px 14px rgba(79,70,229,0.08) !important;
}

.hist-title {
    font-size: 14.5px;
    font-weight: 600;
    color: #111827;
    margin: 0;
    line-height: 1.35;
}
.hist-meta {
    font-size: 11.5px;
    color: #9CA3AF;
    margin: 3px 0 0 0;
}

/* Confidence badge */
.badge-high {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 6px;
    background: #ECFDF5;
    color: #059669;
}
.badge-medium {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 6px;
    background: #FFFBEB;
    color: #D97706;
}
.badge-low {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 6px;
    background: #FEF2F2;
    color: #DC2626;
}
.badge-conflict {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 6px;
    background: #FEE2E2;
    color: #991B1B;
}

/* 3-dot popover button */
/* Bigger & cleaner 3-dot trigger */
div[data-testid="stPopover"] > button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #6B7280 !important;
    font-size: 20px !important;
    font-weight: 700 !important;
    padding: 2px 6px !important;
    min-height: 28px !important;
    line-height: 1 !important;
}
div[data-testid="stPopover"] > button:hover {
    background: #F1F5F9 !important;
    color: #111827 !important;
    border-radius: 6px !important;
}

/* Make the popover menu itself narrower + premium */
div[data-testid="stPopover"] [data-testid="stVerticalBlock"] {
    min-width: 110px !important;
    max-width: 130px !important;
    padding: 4px !important;
}

/* Menu buttons - smaller and tighter */
div[data-testid="stPopover"] button[kind="secondary"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #374151 !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 7px 10px !important;
    min-height: 32px !important;
    border-radius: 6px !important;
    width: 100% !important;
}
div[data-testid="stPopover"] button[kind="secondary"]:hover {
    background: #F1F5F9 !important;
}

/* Delete stays red */
div[class*="st-key-del_"] button {
    color: #DC2626 !important;
}
div[class*="st-key-del_"] button p {
    color: #DC2626 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("History")
st.markdown(
    '<p class="history-sub">The full archive — search and reopen any past conversation</p>',
    unsafe_allow_html=True,
)

if st.session_state.pop("just_loaded_from_history", False):
    st.success("Conversation loaded into Chat.")
    if st.button("Go to Chat →", type="primary"):
        st.switch_page("chat2.py")
    st.divider()

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
conversations = list_conversations(limit=100)
conversations = [c for c in conversations if len(load_conversation_messages(c["id"])) > 0]

if not conversations:
    st.info("No conversations yet. Head to Chat to ask InsightAI something.")
    st.stop()

# ---------------------------------------------------------------------------
# Search only
# ---------------------------------------------------------------------------
search = st.text_input(
    "Search conversations",
    placeholder="Filter by title…",
    label_visibility="collapsed",
)

if search:
    conversations = [
        c for c in conversations
        if search.lower() in (c.get("title") or "").lower()
    ]

if search and not conversations:
    st.info(f'No conversations match “{search}”.')
    st.stop()

st.markdown(
    f'<div class="result-count">{len(conversations)} conversation{"s" if len(conversations) != 1 else ""}</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------
for conv in conversations:
    messages = load_conversation_messages(conv["id"])
    message_count = len(messages)

    last_assistant = next(
        (m for m in reversed(messages) if m["role"] == "assistant"), None
    )

    conf_label = None
    conflict = False
    if last_assistant:
        meta = last_assistant.get("meta") or {}
        conf = meta.get("confidence") or {}
        conf_label = conf.get("label")
        conflict = bool(meta.get("conflict_detected"))

    updated_raw = conv.get("updated_at") or ""
    try:
        dt = datetime.fromisoformat(updated_raw.replace("Z", "+00:00"))
        updated_display = dt.strftime("%b %d, %Y")
    except Exception:
        updated_display = updated_raw[:10] if updated_raw else "—"

    safe_title = (conv.get("title") or "Untitled").replace("$", "\\$")
    conv_id = conv["id"]

    with st.container(border=True):
        # Title row + badges + 3-dot menu
        col_title, col_badges, col_menu = st.columns([5.5, 2.2, 0.6], gap="small")

        with col_title:
            st.markdown(f'<p class="hist-title">{safe_title}</p>', unsafe_allow_html=True)
            st.markdown(
                f'<p class="hist-meta">Updated {updated_display} · {message_count} messages</p>',
                unsafe_allow_html=True,
            )

        with col_badges:
            badges = []
            if conf_label == "High":
                badges.append('<span class="badge-high">High confidence</span>')
            elif conf_label == "Medium":
                badges.append('<span class="badge-medium">Medium confidence</span>')
            elif conf_label == "Low":
                badges.append('<span class="badge-low">Low confidence</span>')
            if conflict:
                badges.append('<span class="badge-conflict">Conflict</span>')

            if badges:
                st.markdown(
                    f'<div style="display:flex; gap:6px; justify-content:flex-end; flex-wrap:wrap; padding-top:2px;">'
                    f'{"".join(badges)}</div>',
                    unsafe_allow_html=True,
                )

        with col_menu:
            with st.popover("⋮"):
                if st.button("Open", key=f"open_{conv_id}", use_container_width=True):
                    st.session_state.conversation_id = conv_id
                    st.session_state.messages = messages
                    st.session_state.just_loaded_from_history = True
                    st.switch_page("chat2.py")

                if st.button("Rename", key=f"rename_{conv_id}", use_container_width=True):
                    st.session_state[f"renaming_{conv_id}"] = True


                if st.button("Delete", key=f"del_{conv_id}", use_container_width=True):
                    delete_conversation(conv_id)
                    if st.session_state.get("conversation_id") == conv_id:
                        st.session_state.conversation_id = None
                        st.session_state.messages = []
                    st.rerun()

        # Inline rename
        if st.session_state.get(f"renaming_{conv_id}"):
            new_title = st.text_input(
                "New title",
                value=conv.get("title") or "",
                key=f"new_title_{conv_id}",
            )
            r1, r2 = st.columns(2)
            with r1:
                if st.button("Save", key=f"save_{conv_id}", use_container_width=True):
                    if new_title.strip():
                        rename_conversation(conv_id, new_title.strip())
                    st.session_state[f"renaming_{conv_id}"] = False
                    st.rerun()
            with r2:
                if st.button("Cancel", key=f"cancel_{conv_id}", use_container_width=True):
                    st.session_state[f"renaming_{conv_id}"] = False
                    st.rerun()

        # Preview
        last_assistant = next((m for m in reversed(messages) if m["role"] == "assistant"), None)
        if last_assistant:
            preview = last_assistant["content"][:240].replace("$", "\\$")
            if len(last_assistant["content"]) > 240:
                preview += "…"
            with st.expander("Preview", expanded=False):
                st.caption(preview)