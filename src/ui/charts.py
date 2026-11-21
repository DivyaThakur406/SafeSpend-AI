"""
Plotly Visualizations for SafeSpend AI.
Modern Dark-Mode Fintech theme with Emerald, Purple, Orange, and Cyan.
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any


CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94A3B8", family="system-ui, -apple-system, sans-serif"),
    margin=dict(l=20, r=20, t=35, b=20),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.35,
        xanchor="center",
        x=0.5,
        font=dict(size=11, color="#CBD5E1")
    )
)

FINTECH_COLORS = [
    "#00F59B",  # Emerald Neon
    "#8B5CF6",  # Electric Purple
    "#F97316",  # Radiant Orange
    "#38BDF8",  # Sky Cyan
    "#EC4899",  # Vivid Pink
    "#FACC15",  # Gold
    "#10B981",  # Mint
    "#6366F1",  # Indigo
    "#14B8A6",  # Teal
    "#F43F5E"   # Rose
]


def create_category_pie_chart(category_df: pd.DataFrame) -> go.Figure:
    """Create a sleek donut chart for expense category distribution."""
    if category_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No expense data recorded yet", showarrow=False, font=dict(color="#94A3B8", size=14))
        fig.update_layout(**CHART_LAYOUT, height=280)
        return fig

    fig = go.Figure(data=[
        go.Pie(
            labels=category_df["category"],
            values=category_df["total_amount"],
            hole=0.62,
            marker=dict(colors=FINTECH_COLORS),
            textinfo="percent",
            hoverinfo="label+value+percent",
            hovertemplate="<b>%{label}</b><br>Total: ₹%{value:,.0f}<br>Share: %{percent}<extra></extra>",
            textfont=dict(color="#FFFFFF", size=11),
        )
    ])

    fig.update_layout(
        **CHART_LAYOUT,
        height=300,
        showlegend=False,
        annotations=[
            dict(
                text="<b>Spend</b><br>Split",
                x=0.5, y=0.5,
                font=dict(size=14, color="#F8FAFC"),
                showarrow=False
            )
        ]
    )
    return fig


def create_daily_spend_bar_chart(daily_df: pd.DataFrame) -> go.Figure:
    """Create daily expense velocity bar chart with glowing bars."""
    if daily_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No daily transactions recorded yet", showarrow=False, font=dict(color="#94A3B8", size=14))
        fig.update_layout(**CHART_LAYOUT, height=260)
        return fig

    fig = go.Figure(data=[
        go.Bar(
            x=daily_df["date"],
            y=daily_df["amount"],
            marker=dict(
                color="#00F59B",
                line=dict(color="#00C878", width=1)
            ),
            hovertemplate="<b>%{x|%d %b}</b><br>Spent: ₹%{y:,.0f}<extra></extra>"
        )
    ])

    fig.update_layout(
        **CHART_LAYOUT,
        height=260,
        xaxis=dict(
            showgrid=False,
            color="#64748B",
            tickformat="%d %b"
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#1E293B",
            color="#64748B",
            tickprefix="₹"
        )
    )
    return fig


def create_upi_distribution_chart(upi_df: pd.DataFrame) -> go.Figure:
    """Create horizontal bar chart of UPI apps usage."""
    if upi_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No UPI data logged", showarrow=False, font=dict(color="#94A3B8", size=14))
        fig.update_layout(**CHART_LAYOUT, height=260)
        return fig

    fig = go.Figure(data=[
        go.Bar(
            y=upi_df["upi_app"],
            x=upi_df["total_amount"],
            orientation="h",
            marker=dict(
                color=["#8B5CF6", "#F97316", "#38BDF8", "#00F59B", "#EC4899", "#A855F7"][:len(upi_df)],
                line=dict(width=0)
            ),
            hovertemplate="<b>%{y}</b><br>Volume: ₹%{x:,.0f}<extra></extra>"
        )
    ])

    fig.update_layout(
        **CHART_LAYOUT,
        height=260,
        xaxis=dict(
            showgrid=True,
            gridcolor="#1E293B",
            color="#64748B",
            tickprefix="₹"
        ),
        yaxis=dict(
            showgrid=False,
            autorange="reversed",
            color="#CBD5E1"
        )
    )
    return fig


def create_cashflow_waterfall(metrics: Dict[str, Any]) -> go.Figure:
    """Create waterfall chart showing how liquid balance resolves to safe-to-spend pool."""
    liquid = metrics["liquid_balance"]
    unpaid_ob = metrics["unpaid_obligations_total"]
    essentials = metrics["remaining_essential_expenses"]
    buffer_and_savings = metrics["emergency_buffer"] + metrics["protected_savings_commitments"]
    safe_spend = metrics["safe_to_spend"]

    fig = go.Figure(go.Waterfall(
        name="Cashflow Waterfall",
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Liquid Cash", "Unpaid Bills", "Remaining Essentials", "Protected Reserves", "Safe-to-Spend"],
        textposition="outside",
        text=[
            f"₹{liquid/1000:.1f}k",
            f"-₹{unpaid_ob/1000:.1f}k",
            f"-₹{essentials/1000:.1f}k",
            f"-₹{buffer_and_savings/1000:.1f}k",
            f"₹{safe_spend/1000:.1f}k"
        ],
        y=[liquid, -unpaid_ob, -essentials, -buffer_and_savings, 0],
        connector={"line": {"color": "#334155"}},
        decreasing={"marker": {"color": "#F97316"}},
        increasing={"marker": {"color": "#00F59B"}},
        totals={"marker": {"color": "#00F59B" if safe_spend > 0 else "#EF4444"}}
    ))

    fig.update_layout(
        **CHART_LAYOUT,
        height=280,
        yaxis=dict(
            showgrid=True,
            gridcolor="#1E293B",
            color="#64748B",
            tickprefix="₹"
        ),
        xaxis=dict(
            color="#CBD5E1",
            tickfont=dict(size=10)
        )
    )
    return fig
