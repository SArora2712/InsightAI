"""
InsightAI - History page.
"""
import streamlit as st

from core.theme2 import apply_theme, confidence_badge_html
from core.history import list_conversations, load_conversation_messages, delete_conversation

st.set_page_config(page_title="InsightAI - History", page_icon="📊", layout="wide")
apply_theme()

st.title("History")
st.caption("Every saved conversation, browsable and reopenable")

if st.session_state.get("just_loaded_from_history"):
    st.success("Conversation loaded.")

    if st.button("Continue to chat →", use_container_width=True):
        st.session_state.just_loaded_from_history = False
        st.switch_page("app.py")

    st.divider()

conversations = list_conversations(limit=100)

if not conversations:
    st.info("No conversations yet. Head to Chat to ask InsightAI something.")
    st.stop()

search = st.text_input("Search conversations", placeholder="Filter by title...", label_visibility="collapsed")
if search:
    conversations = [c for c in conversations if search.lower() in c["title"].lower()]

st.caption(f"{len(conversations)} conversation{'s' if len(conversations) != 1 else ''}")

for conv in conversations:
    messages = load_conversation_messages(conv["id"])
    message_count = len(messages)
    last_assistant_msg = next((m for m in reversed(messages) if m["role"] == "assistant"), None)

    with st.container(border=True):
        col_title, col_meta, col_actions = st.columns([4, 2, 1])

        with col_title:
            safe_title = conv["title"].replace("$", "\\$")
            st.markdown(f"**{safe_title}**")
            st.caption(f"Updated {conv['updated_at'][:10]} · {message_count} messages")

        with col_meta:
            if last_assistant_msg:
                meta = last_assistant_msg.get("meta") or {}
                confidence = meta.get("confidence") or {}
                label = confidence.get("label")
                if label:
                    st.markdown(confidence_badge_html(label, confidence.get("score", 0)), unsafe_allow_html=True)
                if meta.get("conflict_detected"):
                    st.caption(":material/warning: Conflict flagged")

        with col_actions:
            if st.button("Open", key=f"open_{conv['id']}", use_container_width=True, icon=":material/open_in_new:"):
                st.session_state.conversation_id = conv["id"]
                st.session_state.messages = messages
                st.session_state.just_loaded_from_history = True
                st.rerun()
            if st.button("Delete", key=f"del_{conv['id']}", use_container_width=True, icon=":material/delete:"):
                delete_conversation(conv["id"])
                if st.session_state.get("conversation_id") == conv["id"]:
                    st.session_state.conversation_id = None
                    st.session_state.messages = []
                st.rerun()

        with st.expander("Preview"):
            for msg in messages[-4:]:
                role_label = "You" if msg["role"] == "user" else "InsightAI"
                content_preview = msg["content"][:200].replace("$", "\\$")
                st.markdown(f"**{role_label}:** {content_preview}{'...' if len(msg['content']) > 200 else ''}")