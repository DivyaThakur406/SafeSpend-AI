"""
SafeSpend AI - Intelligent Personal Finance Companion for Indian Users.
Main Streamlit Application.
"""
import streamlit as st
import pandas as pd
from datetime import date

# Set page configuration FIRST before any other Streamlit calls
st.set_page_config(
    page_title="SafeSpend AI | Intelligent Personal Finance",
    page_icon="₹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Internal Modules
from src.config import UPI_APPS, EXPENSE_CATEGORIES, INCOME_CATEGORIES
from src.database.db_manager import db
from src.services.safe_spend import SafeSpendEngine
from src.services.transactions import TransactionService
from src.services.coach import AIMoneyCoach
from src.services.affordability import AffordabilitySimulator
from src.services.sms_parser import parse_indian_bank_sms, parse_bank_statement_csv
from src.ui.styles import CUSTOM_CSS
from src.ui.components import (
    render_brand_header,
    render_hero_safe_spend,
    render_kpi_cards,
    render_coach_insights
)
from src.ui.charts import (
    create_category_pie_chart,
    create_daily_spend_bar_chart,
    create_upi_distribution_chart,
    create_cashflow_waterfall
)
from src.utils.formatters import format_inr, format_compact_inr, format_date, sanitize_html
from src.auth.auth_ui import (
    render_landing_page, render_login_page,
    render_signup_page, render_forgot_password_page,
    render_user_profile_sidebar
)

# Inject bold modern fintech styling
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -------------------------------------------------------------
# AUTH GATE
# -------------------------------------------------------------
# Initialize auth state
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "auth_page" not in st.session_state:
    st.session_state["auth_page"] = "landing"
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

# Auth routing — show auth pages if not logged in
if not st.session_state["authenticated"]:
    auth_page = st.session_state.get("auth_page", "landing")
    if auth_page == "login":
        render_login_page()
    elif auth_page == "signup":
        render_signup_page()
    elif auth_page == "forgot_password":
        render_forgot_password_page()
    else:
        render_landing_page()
    st.stop()  # Prevent dashboard from rendering

# Logged in — get user_id for all data calls
user_id = st.session_state["user_id"]


# -------------------------------------------------------------
# SIDEBAR: Profile Settings & Quick Actions
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
        <span style="font-size: 1.6rem; color: #00F59B;">₹</span>
        <span style="font-size: 1.25rem; font-weight: 800; color: #F8FAFC;">SafeSpend AI</span>
    </div>
    """, unsafe_allow_html=True)

    render_user_profile_sidebar(db.get_user_by_id(user_id))
    st.markdown("---")

    profile = db.get_user_profile(user_id)

    st.markdown("### ⚙️ Financial Base")
    with st.expander("💼 Adjust Salary & Commitments", expanded=False):
        new_name = st.text_input("Name", value=profile["full_name"])
        new_income = st.number_input("Monthly Inhand Salary (₹)", value=float(profile["monthly_income"]), step=5000.0)
        new_salary_day = st.number_input("Salary Day of Month", min_value=1, max_value=31, value=int(profile["salary_credit_day"]))
        new_buffer = st.number_input("Emergency Safety Floor (₹)", value=float(profile["emergency_buffer"]), step=2000.0)
        new_balance = st.number_input("Current Liquid Bank Balance (₹)", value=float(profile["current_liquid_balance"]), step=2000.0)
        new_essential_budget = st.number_input("Monthly Essential Budget (₹)", value=float(profile.get("monthly_essential_budget", 18000.0)), step=1000.0)
        new_savings_target = st.number_input("Monthly Protected Savings Target (₹)", value=float(profile.get("monthly_savings_target", 10000.0)), step=1000.0)

        if st.button("Save Profile Settings", use_container_width=True):
            db.update_user_profile(user_id, new_name, new_income, new_salary_day, new_buffer, new_balance, new_essential_budget, new_savings_target)
            st.success("Financial profile updated!")
            st.rerun()

    st.markdown("---")
    st.markdown("### ⚡ Quick Log UPI Spend")
    with st.form("sidebar_quick_tx"):
        quick_amt = st.number_input("Amount (₹)", min_value=1.0, value=250.0, step=50.0)
        quick_merchant = st.text_input("Merchant / Payee", value="Swiggy")
        quick_cat = st.selectbox("Category", EXPENSE_CATEGORIES, index=0)
        quick_upi = st.selectbox("UPI App", UPI_APPS, index=0)
        quick_essential = st.checkbox("Essential Need (Rent/Groceries/Fuel)", value=False)
        
        submitted = st.form_submit_button("Record UPI Payment", use_container_width=True)
        if submitted:
            db.add_transaction(
                user_id,
                tx_date=str(date.today()),
                amount=quick_amt,
                tx_type="expense",
                category=quick_cat,
                upi_app=quick_upi,
                merchant=quick_merchant,
                note="Logged via Quick Action",
                is_essential=1 if quick_essential else 0
            )
            st.success(f"Recorded ₹{quick_amt:,.0f} to {quick_merchant}")
            st.rerun()

    st.markdown("---")
    st.markdown("### 🔄 Salary Cycle Rollover")
    with st.expander("📅 Cycle Management", expanded=False):
        st.caption("Reset recurring commitments for your new salary credit:")
        if st.button("Start Fresh Monthly Cycle", use_container_width=True):
            db.reset_cycle_obligations(user_id)
            st.session_state["survival_override"] = False
            st.success("New salary cycle started! All obligations reset to pending.")
            st.rerun()

    st.markdown("---")
    st.caption("SafeSpend AI v1.0 • Crafted for Indian UPI Ecosystem")


# -------------------------------------------------------------
# MAIN APPLICATION BODY
# -------------------------------------------------------------
survival_override_active = st.session_state.get("survival_override", False)
metrics = SafeSpendEngine.calculate_metrics(user_id=user_id, override_survival=survival_override_active)
render_brand_header(
    user_name=metrics["profile"]["full_name"],
    status=metrics["status"],
    status_color=metrics["status_color"]
)

# Navigation Tabs
tab_dashboard, tab_calculator, tab_upi, tab_coach, tab_simulator, tab_survival = st.tabs([
    "📊 Financial Dashboard",
    "⚡ Safe-to-Spend Engine",
    "📱 UPI Transactions",
    "🤖 AI Money Coach",
    "🛍️ Affordability Simulator",
    "🚨 Survival Mode"
])


# =============================================================
# TAB 1: FINANCIAL DASHBOARD
# =============================================================
with tab_dashboard:
    # Top Hero Dynamic Safe Spend Banner
    render_hero_safe_spend(metrics)

    # 4 Key Telemetry Metrics
    render_kpi_cards(metrics)

    st.markdown("<br>", unsafe_allow_html=True)

    # Visual Analytics Row
    col_chart1, col_chart2 = st.columns([1, 1])

    with col_chart1:
        st.markdown("""
        <div class="fintech-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-weight: 700; font-size: 1.05rem; color: #F8FAFC;">Expense Distribution</span>
                <span class="badge badge-purple">Categories</span>
            </div>
        """, unsafe_allow_html=True)
        cat_df = TransactionService.get_category_breakdown(user_id)
        st.plotly_chart(create_category_pie_chart(cat_df), width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)

    with col_chart2:
        st.markdown("""
        <div class="fintech-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-weight: 700; font-size: 1.05rem; color: #F8FAFC;">Daily Spending Velocity</span>
                <span class="badge badge-green">Timeline</span>
            </div>
        """, unsafe_allow_html=True)
        daily_df = TransactionService.get_daily_spending_trend(user_id)
        st.plotly_chart(create_daily_spend_bar_chart(daily_df), width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)

    # Secondary Row: Cashflow Allocation & Recent UPI Activity
    col_flow, col_recent = st.columns([1, 1.2])

    with col_flow:
        st.markdown("""
        <div class="fintech-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-weight: 700; font-size: 1.05rem; color: #F8FAFC;">Monthly Cashflow Allocation</span>
                <span class="badge badge-orange">Capital Waterfall</span>
            </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(create_cashflow_waterfall(metrics), width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)

    with col_recent:
        st.markdown("""
        <div class="fintech-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-weight: 700; font-size: 1.05rem; color: #F8FAFC;">Recent UPI Transactions</span>
                <span class="badge badge-green">Live Log</span>
            </div>
        """, unsafe_allow_html=True)
        tx_recent = TransactionService.get_enriched_transactions(user_id=user_id, limit=6)
        if not tx_recent.empty:
            for _, r in tx_recent.iterrows():
                is_inc = r["type"] == "income"
                amt_str = f"+{format_inr(r['amount'])}" if is_inc else f"-{format_inr(r['amount'])}"
                amt_color = "#00F59B" if is_inc else "#F8FAFC"
                badge_color = "badge-green" if is_inc else "badge-orange"
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #1E293B;">
                    <div>
                        <div style="font-weight: 600; color: #F8FAFC; font-size: 0.92rem;">{r['merchant']}</div>
                        <div style="font-size: 0.78rem; color: #94A3B8;">{r['date_formatted']} • <span class="badge {badge_color}" style="padding: 2px 8px; font-size: 0.7rem;">{r['upi_app']}</span></div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-weight: 700; color: {amt_color}; font-size: 0.95rem;">{amt_str}</div>
                        <div style="font-size: 0.75rem; color: #64748B;">{r['category'].split('(')[0]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# =============================================================
# TAB 2: DYNAMIC SAFE-TO-SPEND CALCULATOR
# =============================================================
with tab_calculator:
    st.markdown("### ⚡ Dynamic Safe-to-Spend Calculator Engine")
    st.markdown("""
    SafeSpend AI computes your **daily disposable runway** in real time by actively ring-fencing 
    your upcoming fixed bills, remaining essential living costs, savings commitments, and emergency buffer.
    """)

    # --- SECTION 1: FINANCIAL FORMULA & BREAKDOWN ---
    st.markdown(f"""
    <div class="fintech-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="font-weight: 700; font-size: 1.05rem; color: #00F59B;">Core Financial Equation</span>
            <span class="badge badge-green">Zero Debt Impact</span>
        </div>
        <div style="background: #090D18; padding: 18px; border-radius: 12px; font-family: monospace; font-size: 0.92rem; line-height: 1.8; border: 1px solid #1E293B;">
            <span style="color: #94A3B8;">Safe Pool = </span>
            <span style="color: #F8FAFC;">Liquid Balance ({format_inr(metrics['liquid_balance'])})</span>
            <span style="color: #F97316;"> - Upcoming Unpaid Bills ({format_inr(metrics['unpaid_obligations_total'])})</span>
            <span style="color: #38BDF8;"> - Remaining Essentials ({format_inr(metrics['remaining_essential_expenses'])})</span>
            <span style="color: #8B5CF6;"> - Protected Savings ({format_inr(metrics['protected_savings_commitments'])})</span>
            <span style="color: #EC4899;"> - Emergency Buffer ({format_inr(metrics['emergency_buffer'])})</span>
            <br>
            <span style="color: #00F59B; font-weight: bold;">= {format_inr(metrics['safe_to_spend'])} Total Safe Pool</span>
            <br>
            <span style="color: #94A3B8;">Daily Safe-to-Spend = </span>
            <span style="color: #00F59B; font-weight: bold;">{format_inr(metrics['safe_to_spend'])} / {metrics['days_remaining']} Days = {format_inr(metrics['daily_safe_spend'])} / day</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4 Telemetry Cards for the Calculation
    calc_c1, calc_c2, calc_c3, calc_c4 = st.columns(4)
    with calc_c1:
        st.markdown(f"""
        <div style="background: #121A2D; border: 1px solid #1E293B; border-radius: 12px; padding: 16px;">
            <div style="font-size: 0.78rem; color: #94A3B8; text-transform: uppercase;">Active Safe Pool</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: #00F59B; margin: 4px 0;">{format_inr(metrics['safe_to_spend'])}</div>
            <div style="font-size: 0.75rem; color: #94A3B8;">Unencumbered cash</div>
        </div>
        """, unsafe_allow_html=True)
    with calc_c2:
        st.markdown(f"""
        <div style="background: #121A2D; border: 1px solid #1E293B; border-radius: 12px; padding: 16px;">
            <div style="font-size: 0.78rem; color: #94A3B8; text-transform: uppercase;">Days Remaining</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: #38BDF8; margin: 4px 0;">{metrics['days_remaining']} Days</div>
            <div style="font-size: 0.75rem; color: #94A3B8;">Next salary cycle</div>
        </div>
        """, unsafe_allow_html=True)
    with calc_c3:
        st.markdown(f"""
        <div style="background: #121A2D; border: 1px solid #1E293B; border-radius: 12px; padding: 16px;">
            <div style="font-size: 0.78rem; color: #94A3B8; text-transform: uppercase;">Daily Safe Cap</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: #F8FAFC; margin: 4px 0;">{format_inr(metrics['daily_safe_spend'])}</div>
            <div style="font-size: 0.75rem; color: #94A3B8;">Max daily allowance</div>
        </div>
        """, unsafe_allow_html=True)
    with calc_c4:
        st.markdown(f"""
        <div style="background: #121A2D; border: 1px solid #1E293B; border-radius: 12px; padding: 16px;">
            <div style="font-size: 0.78rem; color: #94A3B8; text-transform: uppercase;">Weekend Cap</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: #F97316; margin: 4px 0;">{format_inr(metrics['weekend_safe_spend'])}</div>
            <div style="font-size: 0.75rem; color: #94A3B8;">Sat/Sun +35% weighted</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # What-If Simulator
    with st.container():
        st.markdown("""
        <div class="fintech-card">
            <h4 style="color: #38BDF8; margin-top: 0; margin-bottom: 8px;">🧪 What-If Spend Simulation</h4>
            <p style="color: #94A3B8; font-size: 0.88rem; margin-bottom: 12px;">Test the immediate ripple effect of an impulsive discretionary purchase on your daily allowance.</p>
        """, unsafe_allow_html=True)
        sim_spend = st.slider("Simulate an impulsive spend right now (₹)", 0, 15000, 2000, step=500, key="slider_whatif")
        new_pool = max(0.0, metrics["safe_to_spend"] - sim_spend)
        sim_daily = round(new_pool / metrics["days_remaining"], 2)
        diff = metrics["daily_safe_spend"] - sim_daily

        st.info(f"💡 If you spend **{format_inr(sim_spend)}** today, your daily safe limit for the remaining {metrics['days_remaining']} days will reduce from **{format_inr(metrics['daily_safe_spend'])}** to **{format_inr(sim_daily)}** (-{format_inr(diff)}/day).")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- SECTION 2: FIXED COMMITMENTS & RING-FENCED BILLS ---
    st.markdown("### 📋 Ring-Fenced Fixed Commitments & Monthly Bills")
    st.markdown("Commitments are automatically ring-fenced from your Safe-to-Spend pool so you never miss an EMI, rent, or SIP.")

    obligations_df = db.get_obligations(user_id)
    if not obligations_df.empty:
        total_ob_amt = float(obligations_df["amount"].sum())
        paid_ob_df = obligations_df[obligations_df["is_paid"] == 1]
        unpaid_ob_df = obligations_df[obligations_df["is_paid"] == 0]
        paid_ob_amt = float(paid_ob_df["amount"].sum())
        unpaid_ob_amt = float(unpaid_ob_df["amount"].sum())
        pct_cleared = (paid_ob_amt / max(1.0, total_ob_amt)) * 100

        # Summary Bar
        ob_m1, ob_m2, ob_m3, ob_m4 = st.columns(4)
        with ob_m1:
            st.metric("Total Monthly Bills", format_inr(total_ob_amt))
        with ob_m2:
            st.metric("Cleared to Date", format_inr(paid_ob_amt))
        with ob_m3:
            st.metric("Pending / Upcoming", format_inr(unpaid_ob_amt))
        with ob_m4:
            st.metric("Cleared %", f"{pct_cleared:.0f}%")

        st.progress(pct_cleared / 100)
        st.markdown("<br>", unsafe_allow_html=True)

        # Responsive Obligation Rows
        for _, ob in obligations_df.iterrows():
            is_paid = bool(ob["is_paid"])
            status_text = "PAID" if is_paid else "PENDING"
            status_badge_class = "badge-green" if is_paid else "badge-orange"
            due_text = f"Due Day {ob['due_day']} of month"

            with st.container():
                st.markdown(f"""
                <div style="background: #121A2D; border: 1px solid {'rgba(0, 245, 155, 0.3)' if is_paid else 'rgba(249, 115, 22, 0.3)'}; border-radius: 12px; padding: 14px 18px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                        <div style="display: flex; align-items: center; gap: 14px; min-width: 220px;">
                            <span class="badge {status_badge_class}" style="padding: 4px 12px; font-size: 0.75rem;">{status_text}</span>
                            <div>
                                <div style="font-weight: 700; color: #F8FAFC; font-size: 1.02rem;">{ob['title']}</div>
                                <div style="font-size: 0.78rem; color: #94A3B8;">{ob['category']} • {due_text}</div>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 20px;">
                            <div style="text-align: right;">
                                <div style="font-size: 1.25rem; font-weight: 800; color: {'#00F59B' if is_paid else '#F97316'};">{format_inr(ob['amount'])}</div>
                                <div style="font-size: 0.72rem; color: #64748B;">Fixed Monthly</div>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Action row with clear buttons
                act_c1, act_c2 = st.columns([1, 1])
                with act_c1:
                    if not is_paid:
                        if st.button(f"✓ Mark '{ob['title']}' as Settled", key=f"mark_paid_{ob['id']}", use_container_width=True):
                            db.update_obligation_paid_status(user_id, ob['id'], 1, deduct_from_balance=False)
                            st.success(f"Marked '{ob['title']}' as settled! Safe-to-Spend refreshed.")
                            st.rerun()
                    else:
                        if st.button(f"↩ Revert '{ob['title']}' to Pending", key=f"mark_unpaid_{ob['id']}", use_container_width=True):
                            db.update_obligation_paid_status(user_id, ob['id'], 0, deduct_from_balance=False)
                            st.info(f"Reverted '{ob['title']}' to pending obligation.")
                            st.rerun()
                with act_c2:
                    if not is_paid:
                        if st.button(f"💳 Pay & Deduct ₹{ob['amount']:,.0f} from Bank", key=f"pay_deduct_{ob['id']}", use_container_width=True):
                            db.update_obligation_paid_status(user_id, ob['id'], 1, deduct_from_balance=True)
                            st.success(f"Deducted {format_inr(ob['amount'])} from balance and marked '{ob['title']}' as paid!")
                            st.rerun()
                    else:
                        if st.button(f"🗑️ Delete Commitment", key=f"del_ob_{ob['id']}", use_container_width=True):
                            db.delete_obligation(user_id, ob['id'])
                            st.warning(f"Deleted commitment '{ob['title']}'.")
                            st.rerun()

    # Expander to add new obligation
    with st.expander("➕ Add New Recurring Commitment / EMI", expanded=False):
        with st.form("add_obligation_form_redesigned"):
            ob_title = st.text_input("Commitment Name", placeholder="e.g. JioFiber, Maid Salary, Bike EMI, Term Insurance")
            ob_cat = st.selectbox("Category", EXPENSE_CATEGORIES, index=2)
            ob_amt = st.number_input("Monthly Amount (₹)", min_value=100.0, step=500.0, value=3000.0)
            ob_day = st.number_input("Due Day of Month", min_value=1, max_value=31, value=10)
            add_ob_submit = st.form_submit_button("Save Obligation", use_container_width=True)
            if add_ob_submit and ob_title:
                db.add_obligation(user_id, ob_title, ob_cat, ob_amt, ob_day, 0)
                st.success(f"Added obligation '{ob_title}' for {format_inr(ob_amt)}!")
                st.rerun()

    # --- SECTION 3: SAVINGS GOALS & WEALTH TARGETS ---
    st.markdown("---")
    st.markdown("### 🎯 Active Savings Goals & Wealth Targets")
    st.markdown("Ring-fence dedicated savings funds for emergencies, gadgets, travel, or long-term investments.")

    goals_df = db.get_savings_goals(user_id)
    if not goals_df.empty:
        g_cols = st.columns(min(3, len(goals_df)))
        for idx, (_, g) in enumerate(goals_df.iterrows()):
            col_target = g_cols[idx % len(g_cols)]
            with col_target:
                tgt = float(g["target_amount"])
                curr = float(g["current_amount"])
                pct = min(100.0, (curr / max(1.0, tgt)) * 100)
                clean_title = sanitize_html(g["title"])
                clean_date = sanitize_html(g.get("target_date", "Ongoing"))

                st.markdown(f"""
                <div class="fintech-card" style="padding: 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <span style="font-weight: 700; color: #F8FAFC; font-size: 0.95rem;">{clean_title}</span>
                        <span class="badge badge-purple" style="font-size: 0.68rem;">{pct:.0f}%</span>
                    </div>
                    <div style="font-size: 1.3rem; font-weight: 800; color: #00F59B; margin: 6px 0;">
                        {format_inr(curr)} <span style="font-size: 0.8rem; color: #94A3B8; font-weight: 500;">/ {format_inr(tgt)}</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 8px;">Target Date: {clean_date}</div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(pct / 100.0)

                act_col1, act_col2 = st.columns([1.2, 1])
                with act_col1:
                    if st.button(f"+₹1,000 Saved", key=f"add_1k_g_{g['id']}", use_container_width=True):
                        db.update_savings_goal_progress(user_id, int(g["id"]), 1000.0, deduct_from_balance=True)
                        st.success(f"Added ₹1,000 to {clean_title}!")
                        st.rerun()
                with act_col2:
                    if st.button("🗑️ Delete", key=f"del_g_{g['id']}", use_container_width=True):
                        db.delete_savings_goal(user_id, int(g["id"]))
                        st.warning(f"Deleted goal '{clean_title}'.")
                        st.rerun()

    with st.expander("➕ Create New Savings Target", expanded=False):
        with st.form("add_savings_goal_form"):
            sg_title = st.text_input("Goal Name", placeholder="e.g. Goa Trip, New iPhone, Tax Saver ELSS")
            sg_tgt = st.number_input("Target Amount (₹)", min_value=1000.0, step=5000.0, value=30000.0)
            sg_init = st.number_input("Initial Saved (₹)", min_value=0.0, step=1000.0, value=5000.0)
            sg_date = st.date_input("Target Date", value=date.today())
            sg_submit = st.form_submit_button("Create Savings Goal", use_container_width=True)
            if sg_submit and sg_title:
                db.add_savings_goal(user_id, sg_title, sg_tgt, sg_init, str(sg_date))
                st.success(f"Created goal '{sg_title}'!")
                st.rerun()


# =============================================================
# TAB 3: UPI TRANSACTION MANAGEMENT
# =============================================================
with tab_upi:
    st.markdown("### 📱 UPI Transaction Ledger & Channel Analytics")
    st.markdown("Track and categorize instant payments made across GPay, PhonePe, Paytm, CRED and BHIM.")

    col_tx_list, col_tx_add = st.columns([1.5, 1])

    with col_tx_add:
        st.markdown("""
        <div class="fintech-card">
            <h4 style="color: #00F59B; margin-top: 0;">➕ Add Transaction</h4>
        """, unsafe_allow_html=True)
        with st.form("manual_tx_form"):
            f_type = st.radio("Transaction Type", ["expense", "income"], horizontal=True)
            f_amt = st.number_input("Amount (₹)", min_value=1.0, value=650.0, step=50.0)
            f_merchant = st.text_input("Merchant / Source", value="Blinkit")
            f_cat = st.selectbox("Category", EXPENSE_CATEGORIES if f_type == "expense" else INCOME_CATEGORIES)
            f_upi = st.selectbox("Payment Channel", UPI_APPS)
            f_date = st.date_input("Transaction Date", value=date.today())
            f_note = st.text_input("Note / Tags", placeholder="e.g. Dinner with team")
            f_essential = st.checkbox("Essential Life Expense", value=False)
            
            save_tx = st.form_submit_button("Save to Ledger", use_container_width=True)
            if save_tx:
                db.add_transaction(
                    user_id,
                    tx_date=str(f_date),
                    amount=f_amt,
                    tx_type=f_type,
                    category=f_cat,
                    upi_app=f_upi,
                    merchant=f_merchant,
                    note=f_note,
                    is_essential=1 if f_essential else 0
                )
                st.success("Transaction added to database!")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # UPI App Breakdown Chart
        st.markdown("""
        <div class="fintech-card">
            <h4 style="color: #8B5CF6; margin-top: 0;">UPI App Volume Share</h4>
        """, unsafe_allow_html=True)
        upi_df = TransactionService.get_upi_app_breakdown(user_id)
        st.plotly_chart(create_upi_distribution_chart(upi_df), width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)

    with col_tx_list:
        all_tx = db.get_transactions(user_id)
        if all_tx.empty:
            st.info("No transactions logged yet.")
        else:
            # Filter bar
            filter_cat = st.selectbox("Filter by Category", ["All Categories"] + list(all_tx["category"].unique()))
            if filter_cat != "All Categories":
                display_tx = all_tx[all_tx["category"] == filter_cat]
            else:
                display_tx = all_tx

            st.dataframe(
                display_tx[["date", "type", "merchant", "amount", "category", "upi_app", "note"]],
                width="stretch",
                height=480,
                column_config={
                    "amount": st.column_config.NumberColumn("Amount", format="₹%.0f"),
                    "date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                    "type": st.column_config.TextColumn("Type"),
                    "merchant": st.column_config.TextColumn("Payee"),
                    "category": st.column_config.TextColumn("Category"),
                    "upi_app": st.column_config.TextColumn("Channel")
                }
            )

            # Export Transactions & Bulk Actions
            csv_data = all_tx.to_csv(index=False).encode('utf-8')
            exp_c1, exp_c2 = st.columns([1, 1])
            with exp_c1:
                st.download_button(
                    label="📥 Export Ledger to CSV",
                    data=csv_data,
                    file_name=f"SafeSpend_Transactions_{date.today()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with exp_c2:
                with st.popover("🗑️ Delete Transaction"):
                    del_id = st.number_input("Transaction ID to delete", min_value=1, step=1)
                    if st.button("Confirm Delete", type="secondary"):
                        db.delete_transaction(user_id, del_id)
                        st.success(f"Deleted transaction #{del_id}")
                        st.rerun()

    # --- SECTION: AUTOMATED BANK SMS & STATEMENT INGESTION ---
    st.markdown("---")
    st.markdown("### 📥 Automated Indian Banking Ingestion")
    st.markdown("Avoid manual data entry. Paste raw transaction SMS alerts or upload a bank statement CSV.")

    ingest_col1, ingest_col2 = st.columns([1, 1])

    with ingest_col1:
        st.markdown("""
        <div class="fintech-card">
            <h4 style="color: #00F59B; margin-top: 0;">📲 Instant Bank SMS Parser</h4>
            <p style="font-size: 0.85rem; color: #94A3B8;">Paste SMS alert from HDFC, SBI, ICICI, Axis, PhonePe, GPay or Paytm:</p>
        """, unsafe_allow_html=True)
        sample_sms = "Sent Rs. 450.00 from HDFC Bank to Blue Tokai via UPI on 21-11-2026. Ref 12345"
        raw_sms_input = st.text_area("Bank SMS Text", value="", placeholder=f"e.g. {sample_sms}", height=95)

        if st.button("Parse & Log SMS Transaction", use_container_width=True):
            if raw_sms_input.strip():
                parsed_tx = parse_indian_bank_sms(raw_sms_input)
                if parsed_tx:
                    new_id = db.add_transaction(
                        user_id,
                        tx_date=parsed_tx["date"],
                        amount=parsed_tx["amount"],
                        tx_type=parsed_tx["type"],
                        category=parsed_tx["category"],
                        upi_app=parsed_tx["upi_app"],
                        merchant=parsed_tx["merchant"],
                        note=parsed_tx["note"],
                        is_essential=parsed_tx["is_essential"]
                    )
                    st.success(f"Extracted {format_inr(parsed_tx['amount'])} ({parsed_tx['type']}) to {parsed_tx['merchant']} via {parsed_tx['upi_app']}!")
                    st.rerun()
                else:
                    st.error("Could not extract a valid amount and merchant from the provided text. Please check the SMS format.")
            else:
                st.warning("Please paste an SMS text to parse.")
        st.markdown("</div>", unsafe_allow_html=True)

    with ingest_col2:
        st.markdown("""
        <div class="fintech-card">
            <h4 style="color: #8B5CF6; margin-top: 0;">📄 Bank Statement CSV Importer</h4>
            <p style="font-size: 0.85rem; color: #94A3B8;">Upload Indian bank statement CSV (HDFC, SBI, ICICI, etc.):</p>
        """, unsafe_allow_html=True)
        uploaded_statement = st.file_uploader("Upload Statement CSV", type=["csv"], label_visibility="collapsed")

        if uploaded_statement is not None:
            try:
                stmt_df = pd.read_csv(uploaded_statement)
                parsed_list = parse_bank_statement_csv(stmt_df)
                if parsed_list:
                    st.info(f"Detected {len(parsed_list)} valid transactions in statement.")
                    if st.button(f"Import {len(parsed_list)} Transactions to Ledger", use_container_width=True):
                        inserted = db.add_transactions_batch(user_id, parsed_list)
                        st.success(f"Successfully imported {inserted} transactions! Balance updated.")
                        st.rerun()
                else:
                    st.warning("No valid transactions found in CSV. Expected columns: Date, Narration/Description, Debit/Credit.")
            except Exception as e:
                st.error(f"Error reading CSV file: {e}")
        st.markdown("</div>", unsafe_allow_html=True)


# =============================================================
# TAB 4: AI MONEY COACH
# =============================================================
with tab_coach:
    st.markdown("### 🤖 SafeSpend AI Money Coach")
    st.markdown("Intelligent, proactive nudges engineered around Indian spending psychology and UPI micro-leakage.")

    coach_insights = AIMoneyCoach.get_financial_insights(user_id=user_id)
    render_coach_insights(coach_insights)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 💬 Conversational AI Money Coach")
    st.markdown("Ask any financial question. Your coach executes Python financial calculations using your live balance, pending obligations, and daily safe-to-spend runway.")

    # Initialize conversation history with a data-connected welcome message
    if "coach_messages" not in st.session_state:
        first_name = st.session_state.get("user_name", "User").split()[0]
        st.session_state.coach_messages = [
            {
                "role": "assistant",
                "content": (
                    f"👋 **Namaste {first_name}! I am your SafeSpend AI Money Coach.**\n\n"
                    f"I am connected live to your Indian financial ledger. Right now:\n"
                    f"- **Liquid Bank Cash:** `{format_inr(metrics['liquid_balance'])}`\n"
                    f"- **Active Safe Pool:** `{format_inr(metrics['safe_to_spend'])}` (over `{metrics['days_remaining']} days` left in cycle)\n"
                    f"- **Daily Safe Limit:** `{format_inr(metrics['daily_safe_spend'])} / day`\n\n"
                    f"Ask me any question below — test whether you can afford an upcoming purchase, check your weekly budget, analyze food spends, or simulate what happens if you spend today!"
                )
            }
        ]

    # Quick Suggestion Chips
    st.markdown("##### 💡 Suggested Questions")
    prompt_to_send = None

    q_col1, q_col2, q_col3 = st.columns(3)
    with q_col1:
        if st.button("🛍️ Can I afford a ₹5,000 purchase?", key="chip_afford", use_container_width=True):
            prompt_to_send = "Can I afford a ₹5,000 purchase?"
        if st.button("💰 How much should I save this month?", key="chip_save", use_container_width=True):
            prompt_to_send = "How much should I save this month?"
    with q_col2:
        if st.button("📅 How much can I spend this week?", key="chip_week", use_container_width=True):
            prompt_to_send = "How much can I spend this week?"
        if st.button("⚡ What happens if I spend ₹3,000 today?", key="chip_whatif", use_container_width=True):
            prompt_to_send = "What happens if I spend ₹3,000 today?"
    with q_col3:
        if st.button("🍔 Am I spending too much on food?", key="chip_food", use_container_width=True):
            prompt_to_send = "Am I spending too much on food?"
        if st.button("📋 What bills are due this month?", key="chip_bills", use_container_width=True):
            prompt_to_send = "What bills are due this month?"

    st.markdown("<br>", unsafe_allow_html=True)

    # Chat Input Field and Send Button
    with st.form("coach_chat_form", clear_on_submit=True):
        chat_col_input, chat_col_btn = st.columns([4, 1])
        with chat_col_input:
            input_query = st.text_input(
                "Ask a financial question:",
                placeholder="Type here: e.g. Can I afford a ₹5,000 purchase? Or How much can I spend this week?",
                label_visibility="collapsed"
            )
        with chat_col_btn:
            send_clicked = st.form_submit_button("Send 🚀", use_container_width=True)

        if send_clicked and input_query:
            prompt_to_send = input_query

    # Process new user input if triggered from form or chip
    if prompt_to_send:
        # Append User Message
        st.session_state.coach_messages.append({
            "role": "user",
            "content": prompt_to_send
        })
        # Calculate AI Response using financial tools
        with st.spinner("Analyzing financial ledger and running tools..."):
            ai_reply = AIMoneyCoach.ask(prompt_to_send, user_id=user_id)
            st.session_state.coach_messages.append({
                "role": "assistant",
                "content": ai_reply
            })
        st.rerun()

    # Display Conversation History
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.coach_messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-bubble-user">
                <div class="chat-meta chat-meta-user">👤 You</div>
                <div style="color: #F8FAFC; font-size: 0.95rem; line-height: 1.5;">{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="chat-bubble-ai">
                <div class="chat-meta chat-meta-ai">
                    <span>🤖 SafeSpend Money Coach</span>
                    <span class="badge badge-green" style="font-size: 0.65rem; padding: 2px 8px; margin-left: 8px;">Connected to Financial Tools</span>
                </div>
            """, unsafe_allow_html=True)
            st.markdown(msg["content"])
            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chat Footer & Tools Transparency
    footer_col1, footer_col2 = st.columns([1, 2.5])
    with footer_col1:
        if st.button("🗑️ Clear Conversation History", type="secondary", use_container_width=True):
            st.session_state.coach_messages = []
            st.rerun()
    with footer_col2:
        st.caption("⚙️ **Active Tools:** `get_financial_state()` • `calculate_safe_to_spend()` • `check_upcoming_bills()` • `simulate_purchase()` • `generate_savings_recommendation()`")


# =============================================================
# TAB 5: PURCHASE AFFORDABILITY SIMULATOR
# =============================================================
with tab_simulator:
    st.markdown("### 🛍️ Purchase Affordability Simulator")
    st.markdown("Before buying an expensive gadget, sneakers, or flight ticket, test the exact impact on your daily safe runway.")

    col_sim_in, col_sim_out = st.columns([1, 1.2])

    with col_sim_in:
        st.markdown("""
        <div class="fintech-card">
            <h4 style="color: #00F59B; margin-top: 0;">Item Details</h4>
        """, unsafe_allow_html=True)
        sim_item = st.text_input("Item Name", value="Noise-Cancelling Headphones")
        sim_price = st.number_input("Item Price (₹)", min_value=100.0, value=12999.0, step=500.0)
        sim_mode = st.radio("Payment Method", [
            "Upfront UPI / Card",
            "No-Cost EMI (3 Months)",
            "No-Cost EMI (6 Months)",
            "Standard Bank EMI (12 Months)"
        ])
        sim_tenure = 3 if "3" in sim_mode else (6 if "6" in sim_mode else (12 if "12" in sim_mode else 1))
        
        sim_interest = 0.0
        sim_fee = 0.0
        if "Standard" in sim_mode:
            st.markdown("##### 🏦 Indian Bank EMI Details")
            sim_interest = st.number_input("Annual Interest Rate (%)", min_value=0.0, max_value=36.0, value=15.0, step=0.5)
            sim_fee = st.number_input("Bank Processing Fee (₹)", min_value=0.0, value=199.0, step=50.0)
            st.caption("Includes 18% GST on interest and processing fee as per Indian banking regulations.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_sim_out:
        eval_result = AffordabilitySimulator.evaluate_purchase(
            user_id=user_id,
            item_name=sim_item,
            price=sim_price,
            payment_mode="Upfront UPI / Card" if "Upfront" in sim_mode else "EMI",
            emi_tenure_months=sim_tenure,
            annual_interest_rate=sim_interest,
            processing_fee=sim_fee
        )

        st.markdown(f"""
        <div class="fintech-card" style="border-left: 6px solid {eval_result['verdict_color']};">
            <div style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase;">Simulation Verdict</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: {eval_result['verdict_color']}; margin: 6px 0;">
                {eval_result['verdict']}
            </div>
            <div style="font-size: 0.95rem; color: #E2E8F0; line-height: 1.5; margin-bottom: 16px;">
                {eval_result['advice']}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; background: #0A0E1A; padding: 14px; border-radius: 10px;">
                <div>
                    <div style="font-size: 0.75rem; color: #94A3B8;">Current Daily Safe Limit</div>
                    <div style="font-size: 1.2rem; font-weight: 700; color: #CBD5E1;">{format_inr(eval_result['current_daily'])}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #94A3B8;">New Daily Safe Limit</div>
                    <div style="font-size: 1.2rem; font-weight: 700; color: {eval_result['verdict_color']};">{format_inr(eval_result['new_daily'])}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if eval_result.get("is_emi", False):
            st.markdown(f"""
            <div style="background: #141E34; border: 1px solid #1E293B; border-radius: 12px; padding: 14px 18px; margin-bottom: 14px;">
                <div style="font-weight: 700; color: #C084FC; margin-bottom: 4px;">EMI Amortization Impact</div>
                <div style="font-size: 0.88rem; color: #CBD5E1;">
                    Monthly Obligation: <b>{format_inr(eval_result['monthly_emi'])}</b> for {sim_tenure} months<br>
                    {'Extra Interest + 18% GST: <b>' + format_inr(eval_result['total_extra_cost']) + '</b>' if eval_result['total_extra_cost'] > 0 else 'Zero Cost EMI • No extra interest charged'}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"📌 Lock Purchase & Add as {sim_tenure}-Month EMI Obligation", use_container_width=True):
                clean_item = sanitize_html(sim_item)
                db.add_obligation(
                    user_id,
                    title=f"{clean_item} ({sim_tenure}M EMI)",
                    category="EMI & Debt Repayment",
                    amount=eval_result["monthly_emi"],
                    due_day=15,
                    is_paid=0
                )
                st.success(f"Added '{clean_item}' as a recurring monthly EMI commitment!")
                st.rerun()


# =============================================================
# TAB 6: FINANCIAL SURVIVAL MODE
# =============================================================
with tab_survival:
    st.markdown("### 🚨 Financial Survival Mode")
    st.markdown("""
    When unexpected expenses hit or safe cash falls below your emergency threshold, **Survival Mode** acts as an emergency circuit breaker.
    """)

    col_surv1, col_surv2 = st.columns([1, 1.2])

    with col_surv1:
        st.markdown(f"""
        <div class="fintech-card">
            <h4 style="color: #EF4444; margin-top: 0;">Circuit Breaker Status</h4>
            <div style="font-size: 1.3rem; font-weight: 800; color: {'#EF4444' if metrics['survival_mode'] else '#00F59B'}; margin: 8px 0;">
                {'🚨 ACTIVE (CIRCUIT BREAKER ENGAGED)' if metrics['survival_mode'] else '🟢 NORMAL (SAFE RUNWAY)'}
            </div>
            <p style="color: #94A3B8; font-size: 0.88rem; margin-top: 8px; line-height: 1.5;">
                Survival mode triggers automatically if your Safe Pool reaches ₹0 or if your liquid balance dips below your ₹{metrics['emergency_buffer']:,.0f} emergency safety floor.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🧪 Manual Emergency Circuit Breaker")
        if survival_override_active:
            st.error("⚠️ Manual Emergency Lock is currently ACTIVE across all modules.")
            if st.button("🟢 Deactivate Emergency Lock & Resume Normal Operations", use_container_width=True):
                st.session_state["survival_override"] = False
                st.success("Emergency lock deactivated.")
                st.rerun()
        else:
            if st.button("🚨 Activate Emergency Budget Lock (Simulate Panic Mode)", type="secondary", use_container_width=True):
                st.session_state["survival_override"] = True
                st.warning("Emergency Lock Activated! All daily safe spend allowances locked to ₹0.")
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ Emergency Freeze: Clamp Essentials to ₹5,000 Staples", use_container_width=True):
            p = metrics["profile"]
            db.update_user_profile(
                user_id,
                p["full_name"], p["monthly_income"], p["salary_credit_day"],
                p["emergency_buffer"], p["current_liquid_balance"],
                essential_budget=5000.0,
                savings_target=p.get("monthly_savings_target", 10000.0)
            )
            st.success("Essential expenses budget frozen to bare minimum ₹5,000!")
            st.rerun()

    with col_surv2:
        st.markdown("""
        <div class="fintech-card">
            <h4 style="color: #F97316; margin-top: 0;">Survival Action Protocol</h4>
            <ul style="color: #E2E8F0; line-height: 1.8; font-size: 0.92rem; padding-left: 20px;">
                <li><b>Freeze Discretionary UPI:</b> Delete Swiggy, Zomato, Zepto and Blinkit apps until next salary credit.</li>
                <li><b>Prioritize Non-Negotiable Bills:</b> Ensure Rent, Loan EMIs and domestic staff wages are protected first.</li>
                <li><b>Pause Discretionary Subscriptions:</b> Turn off OTT auto-renewals on CRED / Google Play.</li>
                <li><b>Home-Cooked Staples:</b> Restrict daily food expenses to basic groceries under ₹150/day.</li>
                <li><b>Zero Impulsive Online Shopping:</b> Clear Amazon and Flipkart shopping carts.</li>
                <li><b>Ring-Fence Liquid Cash:</b> Do not break Fixed Deposits or SIPs unless emergency medical bills arise.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
