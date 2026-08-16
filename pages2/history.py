"""
InsightAI - History page (clean + 3-dot menu).
"""
import html
import streamlit as st
from datetime import datetime

from core.theme2 import apply_theme, empty_state, confidence_legend, TEAL, TEAL_SOFT, small_logo_html
from core.text_utils import clean_prose
from core.history import (
    list_conversations_with_messages,
    delete_conversation,
    rename_conversation,
    preview_snippet,
)

st.set_page_config(page_title="InsightAI · History", page_icon="logo/favicon.svg", layout="wide")
apply_theme()
st.markdown(small_logo_html(), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
HISTORY_CSS = """<style>
/* Constrain page width and center on wide screens */
.block-container {
    max-width: 1240px !important;
    margin: 0 auto !important;
}

.history-sub {
    color: #6B7280;
    font-size: 13.5px;
    margin-top: -4px;
    margin-bottom: 20px;
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
    border-color: {TEAL} !important;
    box-shadow: 0 0 0 3px {TEAL_SOFT} !important;
}

.result-count {
    font-size: 12.5px;
    color: #6B7280;
    margin: 10px 0 14px 2px;
}

/* Card */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border: 1px solid #E4E7EC !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 2px rgba(16,24,40,0.04) !important;
    padding: 14px 16px 14px 16px !important;
    margin-bottom: 10px !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #CBD5E1 !important;
    box-shadow: 0 2px 10px rgba(16,32,61,0.06) !important;
}

.hist-title {
    font-size: 16px;
    font-weight: 600;
    color: #10203D;
    margin: 0;
    line-height: 1.35;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.hist-preview {
    font-size: 13px;
    color: #64748B;
    margin: 8px 0 0 0;
    line-height: 1.5;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.hist-meta {
    font-size: 12.5px;
    color: #6B7280;
    margin: 5px 0 0 0;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 5px;
}

/* Collapsible full answer: expander kept inside the card without its own
   chrome so it reads as a subtle teal toggle, not a nested box. */
div[class*="st-key-expand_holder_"] [data-testid="stExpander"] {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    border-radius: 0 !important;
    padding: 0 !important;
    margin: 2px 0 0 !important;
}
div[class*="st-key-expand_holder_"] [data-testid="stExpander"] summary {
    color: #0F766E !important;
    font-size: 12.5px !important;
    font-weight: 500 !important;
    letter-spacing: 0.01em !important;
    padding: 6px 0 2px !important;
    min-height: 0 !important;
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 4px !important;
    width: max-content !important;
    cursor: pointer !important;
}
div[class*="st-key-expand_holder_"] [data-testid="stExpander"] summary:hover {
    text-decoration: underline;
}
/* Hide the native chevron + any stray Material icon so the label is plain
   "Show full answer" with a pointer cursor (nothing can overlap it). */
div[class*="st-key-expand_holder_"] [data-testid="stExpander"] [data-testid="stIconMaterial"],
div[class*="st-key-expand_holder_"] [data-testid="stExpander"] [data-testid^="stExpanderIcon"] {
    display: none !important;
}
div[class*="st-key-expand_holder_"] [data-testid="stExpanderDetails"] {
    border-top: 1px solid #EEF1F5 !important;
    padding-top: 10px !important;
    margin-top: 4px !important;
}
div[class*="st-key-expand_holder_"] [data-testid="stExpanderDetails"] p {
    font-size: 13.5px !important;
    line-height: 1.6 !important;
    color: #334155 !important;
}

/* Subtle metadata chips */
.mode-chip {
    font-size: 11.5px;
    font-weight: 500;
    color: #475569;
    background: #F1F5F9;
    border: 1px solid #E2E8F0;
    border-radius: 5px;
    padding: 2px 7px;
    display: inline-block;
}
.mode-chip::before {
    content: "";
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: {TEAL};
    display: inline-block;
    margin-right: 5px;
    vertical-align: 1px;
}
.conf-chip {
    font-size: 11.5px;
    font-weight: 500;
    border-radius: 5px;
    padding: 2px 7px;
    display: inline-block;
    border: 1px solid transparent;
}
.conf-high   { color: #047857; background: #ECFDF5; border-color: #C6F6D5; }
.conf-medium { color: #B45309; background: #FFFBEB; border-color: #FDE68A; }
.conf-low    { color: #B91C1C; background: #FEF2F2; border-color: #FECACA; }
.conflict-chip {
    font-size: 11.5px;
    font-weight: 500;
    color: #B91C1C;
    background: #FEF2F2;
    border: 1px solid #FECACA;
    border-radius: 5px;
    padding: 2px 7px;
    display: inline-block;
}

/* 3-dot menu trigger: icon-only kebab glyph, never wraps to a vertical column */
div[class*="st-key-menu_"] [data-testid="stPopover"] > button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #6B7280 !important;
    font-size: 18px !important;
    line-height: 20px !important;
    padding: 4px 9px !important;
    min-height: 30px !important;
    min-width: 34px !important;
    width: max-content !important;
    white-space: nowrap !important;
    border-radius: 6px !important;
}
div[class*="st-key-menu_"] [data-testid="stPopover"] > button:hover {
    background: #F1F5F9 !important;
    color: #111827 !important;
}

/* Popover panel: the body renders in a floating portal (data-testid
   "stPopoverBody") OUTSIDE the st-key-menu_ wrapper, so key-scoped rules
   never reach it. Scope instead by the History-only menu buttons it contains
   (open_/del_/rename_/export_ keys never appear anywhere else in the app). */
[data-testid="stPopoverBody"]:has([class*="st-key-open_"]),
[data-testid="stPopoverBody"]:has([class*="st-key-del_"]) {
    min-width: 200px !important;
    max-width: 220px !important;
    width: max-content !important;
    padding: 2px !important;
    border-radius: 8px !important;
}
[data-testid="stPopoverBody"]:has([class*="st-key-open_"]) button,
[data-testid="stPopoverBody"]:has([class*="st-key-open_"]) [data-testid="stBaseButton"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #374151 !important;
    font-weight: 500 !important;
    font-size: 12.5px !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 2px 10px !important;
    min-height: 34px !important;
    border-radius: 6px !important;
    width: 100% !important;
}
[data-testid="stPopoverBody"]:has([class*="st-key-open_"]) button:hover {
    background: #F1F5F9 !important;
    color: #0F172A !important;
}
/* Delete stays red */
div[class*="st-key-del_"] button,
div[class*="st-key-del_"] button p {
    color: #B91C1C !important;
}
[data-testid="stPopoverBody"]:has([class*="st-key-open_"]) hr {
    border-color: #E5E7EB !important;
    margin: 2px 0 !important;
}
</style>
"""

st.markdown(
    HISTORY_CSS.replace("{TEAL}", TEAL).replace("{TEAL_SOFT}", TEAL_SOFT),
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("History")
st.markdown(
    '<p class="history-sub">Review and manage previous analyses</p>',
    unsafe_allow_html=True,
)

if st.session_state.pop("just_loaded_from_history", False):
    st.success("Conversation loaded into Chat.")
    if st.button("Go to Chat →", type="primary"):
        st.switch_page("chat2.py")
    st.divider()

# ---------------------------------------------------------------------------
# Data (single indexed pass - no N+1)
# ---------------------------------------------------------------------------
conversations = list_conversations_with_messages(limit=100)

if not conversations:
    empty_state("No conversations yet — head to Chat to ask InsightAI something.")
    st.stop()

# ---------------------------------------------------------------------------
# Search + sort
# ---------------------------------------------------------------------------
s_col, sort_col = st.columns([3, 1], gap="medium", vertical_alignment="center")
with s_col:
    search = st.text_input(
        "Search conversations",
        placeholder="Search conversations…",
        label_visibility="collapsed",
    )
with sort_col:
    sort_by = st.selectbox(
        "Sort by",
        ["Newest first", "Oldest first", "Title A–Z"],
        label_visibility="collapsed",
    )

if sort_by == "Oldest first":
    conversations = list(reversed(conversations))
elif sort_by == "Title A–Z":
    conversations = sorted(
        conversations, key=lambda c: (c.get("title") or "").lower()
    )

if search:
    conversations = [
        c for c in conversations
        if search.lower() in (c.get("title") or "").lower()
    ]

if search and not conversations:
    empty_state(f"No conversations match “{search}”.")
    st.stop()

st.markdown(
    f'<div class="result-count">{len(conversations)} conversation'
    f'{"s" if len(conversations) != 1 else ""}</div>',
    unsafe_allow_html=True,
)


def conversation_to_markdown(conv: dict, messages: list) -> str:
    """Render a saved conversation as plain Markdown (no DB change)."""
    lines = [f"# {conv.get('title') or 'Untitled'}", "", "---", ""]
    latest = conv.get("updated_at") or ""
    if latest:
        lines.append(f"_Updated {latest[:10]}_")
        lines.append("")
    for m in messages:
        role = "**You**" if m.get("role") == "user" else "**InsightAI**"
        lines.append(f"### {role}")
        lines.append(m.get("content") or "")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------
for conv in conversations:
    messages = conv["messages"]
    message_count = len(messages)
    conv_id = conv["id"]

    safe_title = html.escape(conv.get("title") or "Untitled")

    last_assistant = next(
        (m for m in reversed(messages) if m["role"] == "assistant"), None
    )

    conf_label = None
    conflict = False
    mode = None
    if last_assistant:
        meta = last_assistant.get("meta") or {}
        conf = meta.get("confidence") or {}
        conf_label = conf.get("label")
        conflict = bool(meta.get("conflict_detected"))
        mode = meta.get("mode")

    updated_raw = conv.get("updated_at") or ""
    try:
        dt_obj = datetime.fromisoformat(updated_raw.replace("Z", "+00:00"))
        updated_display = dt_obj.strftime("%b %d, %Y")
    except Exception:
        updated_display = updated_raw[:10] if updated_raw else "—"

    mode_display = (mode or "").replace(" (v1)", "").replace(" (v2)", "")
    meta_chips = []
    if mode_display:
        meta_chips.append(f'<span class="mode-chip">{html.escape(mode_display)}</span>')
    if conf_label:
        conf_class = {"High": "conf-high", "Medium": "conf-medium", "Low": "conf-low"}.get(
            conf_label, ""
        )
        meta_chips.append(
            f'<span class="conf-chip {conf_class}">{html.escape(conf_label)} confidence</span>'
            + confidence_legend()
        )
    if conflict:
        meta_chips.append('<span class="conflict-chip">Conflicting data</span>')

    with st.container(border=True, key=f"hist_card_{conv_id}"):
        # Title + menu trigger
        head_col, menu_col = st.columns(
            [6.3, 0.5], gap="small", vertical_alignment="center"
        )
        with head_col:
            st.markdown(
                f'<p class="hist-title">{safe_title}</p>',
                unsafe_allow_html=True,
            )
        with menu_col:
            with st.popover("⋮", key=f"menu_{conv_id}"):
                if st.button("Open", key=f"open_{conv_id}", use_container_width=True):
                    st.session_state.conversation_id = conv_id
                    st.session_state.messages = messages
                    st.session_state.just_loaded_from_history = True
                    st.switch_page("chat2.py")

                if st.button("Rename", key=f"rename_{conv_id}", use_container_width=True):
                    st.session_state[f"renaming_{conv_id}"] = True

                if st.button("Export…", key=f"export_{conv_id}", use_container_width=True):
                    st.session_state[f"exporting_{conv_id}"] = True

                st.divider()

                if st.button(
                    "Delete conversation",
                    key=f"del_{conv_id}",
                    use_container_width=True,
                ):
                    st.session_state[f"confirm_del_{conv_id}"] = True

        st.markdown(
            f'<div class="hist-meta">'
            f'<span>{updated_display} · {message_count} message'
            f'{"s" if message_count != 1 else ""}</span>'
            f'{ "".join(meta_chips) }'
            f'</div>',
            unsafe_allow_html=True,
        )

        if last_assistant:
            answer_text = last_assistant.get("content") or ""
            if answer_text:
                clean_answer = clean_prose(answer_text)
                st.markdown(
                    f'<p class="hist-preview">{preview_snippet(clean_answer, limit=100)}</p>',
                    unsafe_allow_html=True,
                )
                # Expanded content is bound to THIS card's own conversation:
                # the id comes from the loop variable and the text from this
                # conversation's messages, so cards can never share answers.
                # Chrome-less collapsible: plain "Show full answer" label only.
                # No icon= parameter here — the expander's Material icon renders
                # as a literal-space ligature (stExpanderIcon) that isn't covered
                # by the theme's stIconMaterial font override, leaking garbled
                # text over the label. Native expander toggle stays.
                with st.container(key=f"expand_holder_{conv_id}"):
                    with st.expander("Show full answer", key=f"expand_{conv_id}"):
                        st.markdown(clean_prose(answer_text))

        # ---- Rename (inline) ----
        if st.session_state.get(f"renaming_{conv_id}"):
            new_title = st.text_input(
                "New title",
                value=conv.get("title") or "",
                key=f"new_title_{conv_id}",
            )
            r1, r2 = st.columns(2, gap="small")
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

        # ---- Export (inline) ----
        if st.session_state.get(f"exporting_{conv_id}"):
            export_md = conversation_to_markdown(conv, messages)
            st.download_button(
                "Download Markdown",
                data=export_md,
                file_name=f"insightai_conversation_{conv_id[:8]}.md",
                mime="text/markdown",
                key=f"dl_{conv_id}",
                use_container_width=True,
                icon=":material/download:",
            )

        # ---- Delete confirmation (inline) ----
        if st.session_state.get(f"confirm_del_{conv_id}"):
            st.warning(
                "Delete this conversation and all its messages? "
                "This cannot be undone."
            )
            c1, c2, _ = st.columns([1, 1, 3], gap="small")
            with c1:
                if st.button(
                    "Delete",
                    type="primary",
                    key=f"confirm_yes_{conv_id}",
                    use_container_width=True,
                ):
                    delete_conversation(conv_id)
                    st.session_state.pop(f"confirm_del_{conv_id}", None)
                    st.session_state.pop(f"renaming_{conv_id}", None)
                    st.session_state.pop(f"exporting_{conv_id}", None)
                    if st.session_state.get("conversation_id") == conv_id:
                        st.session_state.conversation_id = None
                        st.session_state.messages = []
                    st.rerun()
            with c2:
                if st.button(
                    "Cancel",
                    key=f"confirm_no_{conv_id}",
                    use_container_width=True,
                ):
                    st.session_state.pop(f"confirm_del_{conv_id}", None)
                    st.rerun()