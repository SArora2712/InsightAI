"""
InsightAI - Minimal session-based login gate (STOPGAP — NOT production auth).

This is deliberately NOT a multi-tenant or secure authentication solution.
It protects the app with a single shared credential so casual visitors can't
open the workspace until a real auth layer (SSO/OAuth/identity provider) is
added. Credentials come from APP_USERNAME / APP_PASSWORD (st.secrets or .env).
The defaults exist only for local development — change them before deploying.
"""
import streamlit as st

from core.envutil import read_env
from core.theme2 import favicon_mark_svg


# Role names. Guests view the full app except admin-only pages (currently
# just the Performance Monitor). Admin comes from the configured credential.
GUEST_ROLE = "guest"
ADMIN_ROLE = "admin"


def expected_username() -> str:
    return read_env("APP_USERNAME", "admin") or "admin"


def expected_password() -> str:
    return read_env("APP_PASSWORD", "insightai") or "insightai"


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated"))


def role() -> str:
    return st.session_state.get("role") or GUEST_ROLE


def is_admin() -> bool:
    """True only for sessions that signed in with the configured credential."""
    return is_authenticated() and role() == ADMIN_ROLE


def authenticate(username: str, password: str) -> bool:
    ok = bool(
        username is not None
        and password is not None
        and username == expected_username()
        and password == expected_password()
    )
    if ok:
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        st.session_state["role"] = ADMIN_ROLE
    return ok


def login_as_guest() -> None:
    """Bypass sign-in for demo/portfolio viewers (no admin abilities)."""
    st.session_state["authenticated"] = True
    st.session_state["username"] = "guest"
    st.session_state["role"] = GUEST_ROLE


def logout() -> None:
    st.session_state.pop("authenticated", None)
    st.session_state.pop("username", None)
    st.session_state.pop("role", None)


def render_login() -> None:
    """Render a minimal, on-brand login form (stopgap only)."""
    st.markdown(
        "<div class='ia-hero' style='margin-top:8vh;'>"
        "<div class='ia-logo'>" + favicon_mark_svg() + "</div>"
        "<div class='ia-hero-name'>Insight<span>AI</span></div>"
        "<div class='ia-hero-sub'>Sign in to continue</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    form_col_l, form_col, form_col_r = st.columns([1, 1, 1], gap="large")
    with form_col:
        with st.form("insightai_login", clear_on_submit=False):
            username = st.text_input(
                "Username", placeholder="Username", key="login_username"
            )
            password = st.text_input(
                "Password", type="password", placeholder="Password", key="login_password"
            )
            submitted = st.form_submit_button(
                "Sign in", type="primary", use_container_width=True
            )
        if submitted:
            if authenticate(username, password):
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown(
            (
                "<div style='text-align:center;color:#94A3B8;font-size:12.5px;"
                "margin:14px 0 6px;'>or</div>"
            ),
            unsafe_allow_html=True,
        )
        if st.button(
            "Continue as Guest",
            key="guest_btn",
            use_container_width=True,
        ):
            login_as_guest()
            st.rerun()
        st.caption("Guests can explore the demo; admin features stay locked.")