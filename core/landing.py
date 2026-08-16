"""
InsightAI - Pre-auth entry experience: landing page + auth view.

This is an ADDITIONAL view layer that controls what renders BEFORE the user
authenticates. It does not touch the auth logic itself (core.auth.authenticate
/ login_as_guest / is_admin / logout are unchanged) - it only decides which
screen to show before st.navigation runs.

View states tracked in st.session_state["view"]:
    "landing"  - default first screen (nav + hero). Entry point.
    "auth"     - secondary view with the existing login card.
    "app"      - the logged-in app (forced whenever the session is
                 authenticated, so an authenticated session can never be
                 bounced back to landing/auth).
"""
import streamlit as st

from core.auth import is_authenticated, login_as_guest, render_login
from core.theme2 import favicon_mark_svg

LANDING_VIEW = "landing"
AUTH_VIEW = "auth"
APP_VIEW = "app"
_VALID_VIEWS = (LANDING_VIEW, AUTH_VIEW, APP_VIEW)

TAGLINE = (
    "AI-powered business analytics — ask questions, get answers "
    "with sources and confidence scores."
)


def current_view() -> str:
    """Return the active pre-auth view, normalizing any bad/injected value.

    An authenticated session is always the app; the landing/auth screens only
    exist while the user is logged out.
    """
    if is_authenticated():
        st.session_state["view"] = APP_VIEW
        return APP_VIEW
    view = st.session_state.get("view", LANDING_VIEW)
    if view not in _VALID_VIEWS:
        view = LANDING_VIEW
    st.session_state["view"] = view
    return view


def _nav_logo() -> str:
    """Small icon + wordmark lockup matching the in-app header style."""
    mark = favicon_mark_svg().strip()
    if mark:
        mark = mark.replace("<svg ", '<svg style="width:34px;height:34px;" ', 1)
    return (
        '<div style="display:flex; align-items:center; gap:10px;">'
        + mark
        + '<span style="font-family:\'Inter\',sans-serif; font-size:19px; '
        'font-weight:700; letter-spacing:-0.5px;">'
        '<span style="color:#10203D;">Insight</span>'
        '<span style="color:#14B8A6;">AI</span>'
        "</span></div>"
    )


def _hero_html() -> str:
    return (
        "<div class='landing-hero'>"
        "<div class='landing-title'>Insight<span>AI</span></div>"
        f"<div class='landing-tagline'>{TAGLINE}</div>"
        "</div>"
    )


def render_landing() -> None:
    """Render the landing entry page: top nav + centered hero only."""
    nav_left, nav_right = st.columns([9, 2], gap="small", vertical_alignment="center")
    with nav_left:
        st.markdown(_nav_logo(), unsafe_allow_html=True)
    with nav_right:
        if st.button(
            "Sign in",
            key="landing_signin_btn",
            type="secondary",
            use_container_width=True,
        ):
            st.session_state["view"] = AUTH_VIEW
            st.rerun()
    st.markdown('<hr class="landing-nav-divider" />', unsafe_allow_html=True)

    st.markdown(_hero_html(), unsafe_allow_html=True)

    # Centered primary CTA (guest path) + secondary link to the auth view.
    cta_left, cta_col, cta_right = st.columns([1, 2, 1], gap="medium")
    with cta_col:
        st.markdown('<div class="landing-cta-gap"></div>', unsafe_allow_html=True)
        if st.button("Try the demo", key="landing_demo_btn", type="primary",
                     use_container_width=True):
            login_as_guest()
            st.session_state["view"] = APP_VIEW
            st.rerun()
        if st.button(
            "Have an account? Sign in", key="hero_signin_btn", type="secondary",
            use_container_width=True,
        ):
            st.session_state["view"] = AUTH_VIEW
            st.rerun()


def render_auth_view() -> None:
    """Render the auth screen: same nav chrome as landing, then the existing
    login card (core.auth.render_login is reused verbatim, not rebuilt)."""
    nav_left, nav_right = st.columns([9, 2], gap="small", vertical_alignment="center")
    with nav_left:
        st.markdown(_nav_logo(), unsafe_allow_html=True)
    with nav_right:
        if st.button(
            "← Back", key="auth_back_btn", type="secondary",
            use_container_width=True,
        ):
            st.session_state["view"] = LANDING_VIEW
            st.rerun()
    st.markdown('<hr class="landing-nav-divider" />', unsafe_allow_html=True)

    render_login()