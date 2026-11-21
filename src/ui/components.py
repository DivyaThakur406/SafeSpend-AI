"""
UI Components for SafeSpend AI.
"""
import streamlit as st
from typing import Dict, Any, List
from src.utils.formatters import format_inr, format_compact_inr, sanitize_html


def render_brand_header(user_name: str, status: str, status_color: str):
    """Render top brand navigation bar with live status indicator."""
    clean_user = sanitize_html(user_name)
    clean_status = sanitize_html(status)
    clean_color = sanitize_html(status_color)
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0 18px 0; border-bottom: 1px solid #1E293B; margin-bottom: 22px;">
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="background: linear-gradient(135deg, #00F59B 0%, #8B5CF6 100%); width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; box-shadow: 0 4px 15px rgba(0, 245, 155, 0.3);">
                ₹
            </div>
            <div>
                <div style="font-size: 1.35rem; font-weight: 800; letter-spacing: -0.5px;">
                    <span style="color: #F8FAFC;">SafeSpend</span><span style="color: #00F59B;"> AI</span>
                </div>
                <div style="font-size: 0.8rem; color: #94A3B8;">Intelligent Personal Finance for India • UPI Ready</div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="background: #121A2D; border: 1px solid #1E293B; padding: 6px 14px; border-radius: 9999px; display: flex; align-items: center; gap: 8px;">
                <span style="width: 8px; height: 8px; border-radius: 50%; background-color: {clean_color}; box-shadow: 0 0 8px {clean_color};"></span>
                <span style="font-size: 0.78rem; font-weight: 700; color: {clean_color}; letter-spacing: 0.5px;">{clean_status}</span>
            </div>
            <div style="background: #141E34; border: 1px solid #28354E; padding: 6px 14px; border-radius: 9999px; font-size: 0.82rem; color: #E2E8F0; font-weight: 600;">
                👤 {clean_user}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_hero_safe_spend(metrics: Dict[str, Any]):
    """Render the central Dynamic Safe-to-Spend banner."""
    if metrics["survival_mode"]:
        st.markdown(f"""
        <div class="survival-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <span class="badge badge-red">⚠️ EMERGENCY ALERT</span>
                    <div class="metric-value-huge-danger">SURVIVAL MODE</div>
                    <div style="color: #FECACA; font-size: 1.05rem; font-weight: 600; margin-top: 4px;">
                        Zero Safe Spend Allowance Remaining
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.85rem; color: #94A3B8;">Days to Next Salary</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: #F8FAFC;">{metrics['days_remaining']} Days</div>
                </div>
            </div>
            <div style="margin-top: 14px; color: #CBD5E1; font-size: 0.92rem; line-height: 1.5; background: rgba(0,0,0,0.25); padding: 12px 16px; border-radius: 10px;">
                Your upcoming obligations ({format_inr(metrics['unpaid_obligations_total'])}), remaining essentials ({format_inr(metrics['remaining_essential_expenses'])}),
                and emergency reserve ({format_inr(metrics['emergency_buffer'])}) exceed your liquid bank balance ({format_inr(metrics['liquid_balance'])}).
                All discretionary UPI and shopping spends must be paused immediately.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        daily_val = format_inr(metrics["daily_safe_spend"])
        weekly_val = format_inr(metrics["weekly_safe_spend"])
        weekend_val = format_inr(metrics["weekend_safe_spend"])
        safe_pool_val = format_inr(metrics["safe_to_spend"])

        st.markdown(f"""
        <div class="hero-safe-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="badge badge-green">DYNAMIC ALGORITHM</span>
                        <span class="badge badge-purple">SAFE POOL: {safe_pool_val}</span>
                    </div>
                    <div style="font-size: 0.95rem; color: #94A3B8; margin-top: 8px; font-weight: 500;">
                        Today's Safe-to-Spend Limit
                    </div>
                    <div class="metric-value-huge">
                        {daily_val}
                        <span style="font-size: 1.1rem; color: #94A3B8; font-weight: 500;">/ day</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #CBD5E1;">
                        Guaranteed zero debt impact • Keeps ₹{metrics['emergency_buffer']:,.0f} emergency cushion + {format_inr(metrics['remaining_essential_expenses'])} essentials safe
                    </div>
                </div>
                <div style="display: flex; gap: 18px; align-items: center; background: rgba(10, 14, 26, 0.45); padding: 16px 20px; border-radius: 14px; border: 1px solid #1E293B; flex-wrap: wrap;">
                    <div style="text-align: center; border-right: 1px solid #1E293B; padding-right: 16px;">
                        <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase;">Days Left</div>
                        <div style="font-size: 1.55rem; font-weight: 800; color: #38BDF8;">{metrics['days_remaining']}</div>
                        <div style="font-size: 0.72rem; color: #64748B;">in cycle</div>
                    </div>
                    <div style="text-align: center; border-right: 1px solid #1E293B; padding-right: 16px;">
                        <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase;">7-Day Cap</div>
                        <div style="font-size: 1.35rem; font-weight: 700; color: #8B5CF6;">{weekly_val}</div>
                        <div style="font-size: 0.72rem; color: #64748B;">rolling</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase;">Weekend Cap</div>
                        <div style="font-size: 1.35rem; font-weight: 700; color: #F97316;">{weekend_val}</div>
                        <div style="font-size: 0.72rem; color: #64748B;">Sat/Sun boost</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_kpi_cards(metrics: Dict[str, Any]):
    """Render top financial telemetry KPIs reflecting the exact 5-term formula."""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="fintech-card">
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px;">1. Liquid Cash</div>
            <div style="font-size: 1.45rem; font-weight: 800; color: #F8FAFC; margin: 4px 0;">{format_inr(metrics['liquid_balance'])}</div>
            <div style="font-size: 0.74rem; color: #00F59B;">● Available in bank</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="fintech-card">
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px;">2. Unpaid Bills</div>
            <div style="font-size: 1.45rem; font-weight: 800; color: #F97316; margin: 4px 0;">{format_inr(metrics['unpaid_obligations_total'])}</div>
            <div style="font-size: 0.74rem; color: #94A3B8;">{len(metrics['unpaid_items'])} pending commitments</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="fintech-card">
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px;">3. Remaining Essentials</div>
            <div style="font-size: 1.45rem; font-weight: 800; color: #38BDF8; margin: 4px 0;">{format_inr(metrics['remaining_essential_expenses'])}</div>
            <div style="font-size: 0.74rem; color: #94A3B8;">{format_inr(metrics['essential_spent_this_cycle'])} spent to date</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        reserve_total = metrics['emergency_buffer'] + metrics['protected_savings_commitments']
        st.markdown(f"""
        <div class="fintech-card">
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px;">4. Protected Buffer</div>
            <div style="font-size: 1.45rem; font-weight: 800; color: #8B5CF6; margin: 4px 0;">{format_inr(reserve_total)}</div>
            <div style="font-size: 0.74rem; color: #94A3B8;">Buffer + SIP commitments</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        score = metrics["health_score"]
        score_color = "#00F59B" if score >= 75 else ("#F97316" if score >= 50 else "#EF4444")
        st.markdown(f"""
        <div class="fintech-card">
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px;">Health Score</div>
            <div style="font-size: 1.45rem; font-weight: 800; color: {score_color}; margin: 4px 0;">{score} / 100</div>
            <div style="font-size: 0.74rem; color: {score_color}; font-weight: 600;">Status: {metrics['status']}</div>
        </div>
        """, unsafe_allow_html=True)


def render_coach_insights(insights: List[Dict[str, Any]]):
    """Render smart AI Money Coach advisory cards."""
    for item in insights:
        box_class = {
            "danger": "coach-box-danger",
            "success": "coach-box-green",
            "warning": "coach-box-orange",
            "purple": "coach-box",
            "cyan": "coach-box"
        }.get(item["type"], "coach-box")

        badge_class = {
            "danger": "badge-red",
            "success": "badge-green",
            "warning": "badge-orange",
            "purple": "badge-purple",
            "cyan": "badge-green"
        }.get(item["type"], "badge-purple")

        st.markdown(f"""
        <div class="{box_class}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span class="badge {badge_class}">{item['badge']}</span>
                <span style="font-size: 0.75rem; color: #94A3B8; font-weight: 500;">Actionable Insight</span>
            </div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #F8FAFC; margin-bottom: 6px;">
                {item['title']}
            </div>
            <div style="font-size: 0.9rem; color: #CBD5E1; line-height: 1.45;">
                {item['message']}
            </div>
        </div>
        """, unsafe_allow_html=True)
