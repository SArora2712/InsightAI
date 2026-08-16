"""Tests for the confidence trend chart styling (Item 4).

The line chart must show data-point markers, a subtle teal area fill, and
light-but-visible gridlines, without switching chart libraries.
"""
import pandas as pd
import pytest

from pages2.dashboard import build_confidence_trend_figure


def _df(points):
    return pd.DataFrame({"time": points, "score": [0.8, 0.9, 0.6, 1.0, 0.75]})


@pytest.fixture()
def fig():
    return build_confidence_trend_figure(
        pd.DataFrame({
            "time": ["2026-08-01 10:00", "2026-08-02 11:00", "2026-08-03 12:00"],
            "score": [0.6, 0.8, 0.9],
        })
    )


def test_line_uses_markers_and_area_fill(fig):
    trace = fig.data[0]
    assert trace.mode == "lines+markers"
    # Visible data-point markers (circles) sized to read on the line.
    assert trace.marker.size == 7
    assert trace.marker.line.width >= 2
    # Subtle teal gradient/area fill beneath the line.
    assert trace.fill == "tozeroy"
    assert trace.fillcolor == "rgba(20,184,166,0.16)"


def test_markers_share_line_color(fig):
    trace = fig.data[0]
    assert trace.marker.color == trace.line.color


def test_gridlines_visible_but_light(fig):
    yaxis = fig.layout.yaxis
    assert yaxis.showgrid is True
    assert yaxis.gridcolor == "#E7EAF1"
    assert yaxis.gridwidth >= 1


def test_axis_labels_kept(fig):
    assert fig.layout.xaxis.tickfont.size == 11
    assert tuple(fig.layout.yaxis.range) == (0, 1.08)