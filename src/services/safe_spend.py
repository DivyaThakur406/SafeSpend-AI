"""
Dynamic Safe-to-Spend Calculator Engine.
Implements the exact financial formula:
    Safe Pool =
        Liquid Balance
        - Upcoming Unpaid Obligations
        - Remaining Essential Expenses
        - Protected Savings Commitments
        - Emergency Buffer

    Safe-to-Spend = max(0, Safe Pool)
    Daily Safe-to-Spend = Safe-to-Spend / Days Remaining

Avoids double-counting expenses already paid or deducted from the balance.
"""
import calendar
from datetime import date, datetime
from typing import Dict, Any, List
import pandas as pd

from src.database.db_manager import db


class SafeSpendEngine:
    @staticmethod
    def calculate_metrics(user_id: int = 1, override_survival: bool = False) -> Dict[str, Any]:
        profile = db.get_user_profile(user_id)
        obligations_df = db.get_obligations(user_id)

        today = date.today()
        current_year = today.year
        current_month = today.month
        current_day = today.day

        # Days in current calendar month
        _, days_in_month = calendar.monthrange(current_year, current_month)

        # Salary day (default 1st)
        salary_day = profile.get("salary_credit_day", 1)

        # Calculate days until next salary credit
        if current_day < salary_day:
            days_remaining = salary_day - current_day
        else:
            days_remaining = (days_in_month - current_day) + salary_day
        days_remaining = max(1, days_remaining)

        # 1. Liquid Balance
        liquid_balance = float(profile.get("current_liquid_balance", 0.0))

        # 2. Upcoming Unpaid Obligations (Non-Savings Fixed Commitments)
        unpaid_obligations_total = 0.0
        total_monthly_obligations = 0.0
        unpaid_items: List[Dict[str, Any]] = []
        paid_items: List[Dict[str, Any]] = []

        # 3. Protected Savings Commitments (Unpaid SIPs & Goal Allocations)
        protected_savings_commitments = 0.0

        if not obligations_df.empty:
            total_monthly_obligations = float(obligations_df["amount"].sum())

            # Identify savings / investment obligations (e.g. SIPs)
            is_savings_ob = obligations_df["category"].str.contains(
                "Investment|SIP|Mutual Funds|Savings", case=False, na=False
            )
            savings_df = obligations_df[is_savings_ob]
            fixed_bills_df = obligations_df[~is_savings_ob]

            # Unpaid fixed bills
            unpaid_bills_df = fixed_bills_df[fixed_bills_df["is_paid"] == 0]
            unpaid_obligations_total = float(unpaid_bills_df["amount"].sum())
            unpaid_items = unpaid_bills_df.to_dict(orient="records")

            # Paid items
            paid_df = obligations_df[obligations_df["is_paid"] == 1]
            paid_items = paid_df.to_dict(orient="records")

            # Unpaid SIP / Investment commitments
            unpaid_savings_df = savings_df[savings_df["is_paid"] == 0]
            protected_savings_commitments = float(unpaid_savings_df["amount"].sum())
            if not unpaid_savings_df.empty:
                unpaid_items.extend(unpaid_savings_df.to_dict(orient="records"))

        # 4. Remaining Essential Expenses
        # Calculate monthly essential budget and how much has already been spent
        monthly_essential_budget = float(profile.get("monthly_essential_budget", 18000.0))
        
        tx_df = db.get_transactions(user_id)
        essential_spent_this_cycle = 0.0
        total_spent_this_month = 0.0
        upi_spent_this_month = 0.0

        if not tx_df.empty:
            tx_df_copy = tx_df.copy()
            tx_df_copy["date_dt"] = pd.to_datetime(tx_df_copy["date"])
            this_month_tx = tx_df_copy[
                (tx_df_copy["date_dt"].dt.month == current_month) &
                (tx_df_copy["date_dt"].dt.year == current_year) &
                (tx_df_copy["type"] == "expense")
            ]
            total_spent_this_month = float(this_month_tx["amount"].sum())
            
            # UPI spend velocity
            upi_tx = this_month_tx[this_month_tx["upi_app"].str.contains("Pay|GPay|CRED|BHIM", case=False, na=False)]
            upi_spent_this_month = float(upi_tx["amount"].sum())

            # Essential variable expenses already paid and deducted from liquid balance:
            # Exclude fixed obligations like rent/EMI/SIP to avoid overlap with obligations table
            non_fixed_essential = this_month_tx[
                (this_month_tx["is_essential"] == 1) &
                (~this_month_tx["category"].str.contains("Rent|EMI|Debt|Investment|SIP", case=False, na=False))
            ]
            essential_spent_this_cycle = float(non_fixed_essential["amount"].sum())

        # Remaining essential budget for the rest of the cycle:
        # Cannot be negative; once spent, it is already deducted from liquid balance so deduction becomes 0
        remaining_essential_expenses = max(0.0, monthly_essential_budget - essential_spent_this_cycle)

        # 5. Emergency Buffer
        emergency_buffer = float(profile.get("emergency_buffer", 15000.0))

        # --- FINANCIAL FORMULA ---
        # Safe Pool = Liquid Balance
        #             - Upcoming Unpaid Obligations
        #             - Remaining Essential Expenses
        #             - Protected Savings Commitments
        #             - Emergency Buffer
        raw_safe_pool = (
            liquid_balance
            - unpaid_obligations_total
            - remaining_essential_expenses
            - protected_savings_commitments
            - emergency_buffer
        )

        safe_to_spend = max(0.0, raw_safe_pool)
        daily_safe_spend = round(safe_to_spend / days_remaining, 2)
        weekly_safe_spend = round(daily_safe_spend * 7, 2)
        weekend_safe_spend = round(daily_safe_spend * 1.35, 2)

        # Survival Mode Trigger: Safe Pool <= 0 or Liquid Balance < Emergency Buffer or Manual Override
        natural_survival = (raw_safe_pool <= 0) or (liquid_balance < emergency_buffer)
        survival_mode = natural_survival or override_survival

        if survival_mode:
            daily_safe_spend = 0.0
            weekly_safe_spend = 0.0
            weekend_safe_spend = 0.0
            status = "SURVIVAL MODE (MANUAL)" if override_survival and not natural_survival else "CRITICAL / SURVIVAL"
            status_color = "#EF4444"
            health_score = max(5, int((liquid_balance / max(emergency_buffer, 1)) * 30))
        else:
            # Health Score Evaluation
            income = float(profile.get("monthly_income", 100000.0))
            daily_ratio = daily_safe_spend / max(1.0, (income / 30))
            if daily_ratio > 0.35:
                status = "EXCELLENT"
                status_color = "#00F59B"
                health_score = min(98, 85 + int(daily_ratio * 15))
            elif daily_ratio > 0.15:
                status = "BALANCED"
                status_color = "#8B5CF6"
                health_score = 75
            else:
                status = "TIGHT"
                status_color = "#F97316"
                health_score = 55

        return {
            "profile": profile,
            "today": today,
            "current_day": current_day,
            "days_remaining": days_remaining,
            "liquid_balance": liquid_balance,
            "emergency_buffer": emergency_buffer,
            "unpaid_obligations_total": unpaid_obligations_total,
            "total_monthly_obligations": total_monthly_obligations,
            "unpaid_items": unpaid_items,
            "paid_items": paid_items,
            "monthly_essential_budget": monthly_essential_budget,
            "essential_spent_this_cycle": essential_spent_this_cycle,
            "remaining_essential_expenses": remaining_essential_expenses,
            "protected_savings_commitments": protected_savings_commitments,
            "raw_pool": raw_safe_pool,
            "safe_pool": safe_to_spend,
            "safe_to_spend": safe_to_spend,
            "daily_safe_spend": daily_safe_spend,
            "weekly_safe_spend": weekly_safe_spend,
            "weekend_safe_spend": weekend_safe_spend,
            "survival_mode": survival_mode,
            "status": status,
            "status_color": status_color,
            "health_score": health_score,
            "total_spent_this_month": total_spent_this_month,
            "upi_spent_this_month": upi_spent_this_month,
        }
