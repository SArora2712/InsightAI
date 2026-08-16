"""AppTest tests for the Dashboard KPI split (Fix 5).

The metrics row is split into two *labeled* groups: "Business metrics"
(Total revenue) and "AI system health" (Avg confidence, Conflicts flagged,
Documents indexed). Each KPI card must render under the correct group.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

DASHBOARD_PY = str(Path(__file__).resolve().parents[1] / "pages2" / "dashboard.py")

BUSINESS_HEADING = "Business metrics"
HEALTH_HEADING = "AI system health"


def _run_dashboard():
    at = AppTest.from_file(DASHBOARD_PY, default_timeout=120)
    at.session_state["authenticated"] = True
    at.session_state["role"] = "admin"
    at.session_state["username"] = "admin"
    at.run()
    assert not at.exception
    return at


def _ordered_elements(at):
    """[(kind, identity)] in render order, across all element types."""
    out = []
    for el in at.main:
        if type(el).__name__ == "Markdown":
            out.append(("markdown", el.value))
        elif type(el).__name__ == "Metric":
            out.append(("metric", el.label))
    return out


def test_both_section_labels_render():
    at = _run_dashboard()
    kinds = [k for k, _ in _ordered_elements(at)]
    assert kinds.count("metric") == 5
    assert sum(k == "markdown" and v == f"##### {BUSINESS_HEADING}" for k, v in _ordered_elements(at)) == 1
    assert sum(k == "markdown" and v == f"##### {HEALTH_HEADING}" for k, v in _ordered_elements(at)) == 1


def test_each_kpi_appears_under_correct_group():
    at = _run_dashboard()
    elements = _ordered_elements(at)

    def index_of(kind, identity):
        for i, (k, v) in enumerate(elements):
            if k == kind and identity in v:
                return i
        raise AssertionError(f"missing {kind} {identity!r}")

    biz_marker = index_of("markdown", BUSINESS_HEADING)
    health_marker = index_of("markdown", HEALTH_HEADING)

    revenue = index_of("metric", "Total revenue")
    orders = index_of("metric", "Total orders")
    avg_conf = index_of("metric", "Avg confidence")
    conflicts = index_of("metric", "Conflicts flagged")
    docs = index_of("metric", "Documents indexed")

    # Both business cards sit between their label and the health label.
    assert biz_marker < revenue < orders < health_marker
    # Health cards all come after the health label.
    assert health_marker < min(avg_conf, conflicts, docs)


def test_metric_labels_are_unchanged():
    at = _run_dashboard()
    labels = [m.label for m in at.metric]
    assert labels == [
        "Total revenue",
        "Total orders",
        "Avg confidence",
        "Conflicts flagged",
        "Documents indexed",
    ]