"""Regression tests for the shared currency/number formatting helpers.

Guards against drifting "abbreviated" vs "full" money displays (the old
"$92.2M" vs "$92,200,000" mismatch), None inputs, and dollar escaping.
"""
import pytest

from core.formatting import format_currency, format_number


def test_abbreviated_millions():
    assert format_currency(448_386_633) == "$448.4M"


def test_abbreviated_billions():
    assert format_currency(1_250_000_000) == "$1.2B"


def test_abbreviated_thousands():
    assert format_currency(92_200) == "$92.2K"


def test_abbreviated_small_values_no_suffix():
    assert format_currency(924) == "$924"


def test_abbreviated_negative():
    assert format_currency(-448_386_633) == "-$448.4M"


def test_full_style_exact_commas():
    assert format_currency(448_386_633, style="full") == "$448,386,633"


def test_full_style_with_decimals():
    assert format_currency(19.9542, style="full", decimals=2) == "$19.95"


def test_none_returns_dash():
    assert format_currency(None) == "—"


def test_non_numeric_returns_dash():
    assert format_currency("oops") == "—"


def test_zero():
    assert format_currency(0) == "$0"


def test_format_number_grouping():
    assert format_number(1234567) == "1,234,567"


def test_format_number_decimals():
    assert format_number(3.14159, decimals=2) == "3.14"


def test_format_number_none():
    assert format_number(None) == "—"


@pytest.mark.parametrize(
    "style,expected",
    [
        ("abbreviated", "$448.4M"),
        ("full", "$448,386,633"),
    ],
)
def test_styles_are_deterministic_same_input(style, expected):
    assert format_currency(448_386_633, style=style) == expected