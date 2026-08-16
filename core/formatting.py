"""
InsightAI - Shared number/currency formatting.

Single source of truth for how money is displayed so KPI cards
("$448.4M") and detailed figures ("$448,386,633") can never drift apart
again. Pure module (no Streamlit import) so tests and non-UI code can use it.
"""


def format_currency(
    value,
    style: str = "abbreviated",
    decimals: int | None = None,
) -> str:
    """
    Format a numeric value as a currency string.

    style="abbreviated": human-scale KPI ("$448.4M", "$1.2B") - for dashboard
        summary cards.
    style="full": exact figure ("$448,386,633") - for detailed analysis blocks.

    `decimals` overrides the per-style default (abbreviated=1, full=0).
    """
    if value is None:
        return "—"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "—"

    sign = "-" if value < 0 else ""
    value = abs(value)
    if style != "full":
        abs_v = value
        if abs_v >= 1e9:
            divisor, suffix = 1e9, "B"
        elif abs_v >= 1e6:
            divisor, suffix = 1e6, "M"
        elif abs_v >= 1e3:
            divisor, suffix = 1e3, "K"
        else:
            divisor, suffix = 1.0, ""
        if decimals is None:
            decimals = 1 if suffix else 0
        return f"{sign}${value / divisor:,.{decimals}f}{suffix}"

    if decimals is None:
        decimals = 0
    return f"{sign}${value:,.{decimals}f}"


def format_number(value, decimals: int = 0) -> str:
    """Grouped integer/decimal without a currency symbol (orders, counts)."""
    if value is None:
        return "—"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "—"
    return f"{value:,.{decimals}f}"