"""
Formatters for Indian Financial Systems:
- Indian Rupee (₹) formatting with lakhs and crores
- Date and time formatters
"""
from datetime import datetime, date
from typing import Union, Any
import html


def sanitize_html(text: Any) -> str:
    """Sanitize user input to prevent XSS when embedding in HTML."""
    if text is None:
        return ""
    return html.escape(str(text))


def format_inr(amount: Union[int, float], include_symbol: bool = True, decimals: int = 0) -> str:
    """
    Format a number in the Indian numbering system:
    1,00,000 instead of 100,000.
    1,00,00,000 instead of 10,000,000.
    """
    if amount is None:
        amount = 0.0

    is_negative = amount < 0
    amount = abs(amount)

    if decimals > 0:
        base_format = f"{amount:.{decimals}f}"
        integer_part, decimal_part = base_format.split(".")
        decimal_str = f".{decimal_part}"
    else:
        integer_part = str(int(round(amount)))
        decimal_str = ""

    # Indian numbering grouping: last 3 digits, then groups of 2
    if len(integer_part) <= 3:
        formatted_int = integer_part
    else:
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted_int = ",".join(groups) + "," + last_three

    result = f"{formatted_int}{decimal_str}"
    if is_negative:
        result = f"-{result}"

    return f"₹{result}" if include_symbol else result


def format_compact_inr(amount: Union[int, float]) -> str:
    """Format large sums compactly for dashboard KPIs (e.g., ₹1.25 L, ₹2.5 Cr, ₹8.4 K)."""
    if amount is None:
        return "₹0"
    
    sign = "-" if amount < 0 else ""
    abs_amt = abs(amount)

    if abs_amt >= 10_000_000:
        return f"{sign}₹{abs_amt / 10_000_000:.2f} Cr"
    elif abs_amt >= 100_000:
        return f"{sign}₹{abs_amt / 100_000:.2f} L"
    elif abs_amt >= 1_000:
        return f"{sign}₹{abs_amt / 1_000:.1f} K"
    else:
        return f"{sign}₹{abs_amt:.0f}"


def format_date(dt: Union[str, date, datetime]) -> str:
    """Format date to friendly Indian business format (e.g. 21 Nov 2026)."""
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, "%Y-%m-%d").date()
        except ValueError:
            return dt
    return dt.strftime("%d %b %Y")
