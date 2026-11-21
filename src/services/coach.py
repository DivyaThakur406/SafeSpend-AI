"""
AI Money Coach Engine.
Features:
1. Proactive financial nudges and behavioral diagnosis.
2. Official Financial Tools:
   - get_financial_state()
   - calculate_safe_to_spend()
   - check_upcoming_bills()
   - simulate_purchase()
   - generate_savings_recommendation()
3. Conversational AI Assistant with deterministic tool routing and rule-based fallback.
"""
import re
import os
from typing import List, Dict, Any, Optional, Tuple
from src.services.safe_spend import SafeSpendEngine
from src.services.affordability import AffordabilitySimulator
from src.database.db_manager import db
from src.utils.formatters import format_inr, format_compact_inr


# =============================================================
# OFFICIAL FINANCIAL TOOLS
# =============================================================

def get_financial_state(user_id: int = 1) -> Dict[str, Any]:
    """
    Returns the real-time financial telemetry of the user.
    Uses actual calculations from SQLite and SafeSpendEngine.
    """
    metrics = SafeSpendEngine.calculate_metrics(user_id)
    return {
        "liquid_balance": metrics["liquid_balance"],
        "monthly_income": float(metrics["profile"].get("monthly_income", 100000.0)),
        "days_remaining": metrics["days_remaining"],
        "unpaid_obligations_total": metrics["unpaid_obligations_total"],
        "total_monthly_obligations": metrics["total_monthly_obligations"],
        "remaining_essential_expenses": metrics["remaining_essential_expenses"],
        "protected_savings_commitments": metrics["protected_savings_commitments"],
        "emergency_buffer": metrics["emergency_buffer"],
        "safe_to_spend": metrics["safe_to_spend"],
        "daily_safe_spend": metrics["daily_safe_spend"],
        "weekly_safe_spend": metrics["weekly_safe_spend"],
        "weekend_safe_spend": metrics["weekend_safe_spend"],
        "health_score": metrics["health_score"],
        "status": metrics["status"],
        "survival_mode": metrics["survival_mode"],
        "total_spent_this_month": metrics["total_spent_this_month"],
        "essential_spent_this_cycle": metrics["essential_spent_this_cycle"]
    }


def calculate_safe_to_spend(user_id: int = 1, what_if_spend: float = 0.0) -> Dict[str, Any]:
    """
    Calculates active safe pool and daily allowance.
    If what_if_spend > 0, calculates exact post-spend runway and daily reduction.
    """
    metrics = SafeSpendEngine.calculate_metrics(user_id)
    current_pool = metrics["safe_to_spend"]
    days_left = metrics["days_remaining"]
    current_daily = metrics["daily_safe_spend"]

    if what_if_spend > 0:
        new_pool = max(0.0, current_pool - what_if_spend)
        new_daily = round(new_pool / days_left, 2)
        daily_reduction = round(current_daily - new_daily, 2)
        breached = what_if_spend > current_pool
        return {
            "current_pool": current_pool,
            "current_daily": current_daily,
            "what_if_spend": what_if_spend,
            "new_pool": new_pool,
            "new_daily": new_daily,
            "daily_reduction": daily_reduction,
            "days_remaining": days_left,
            "breached": breached,
            "emergency_buffer_impact": max(0.0, what_if_spend - current_pool)
        }

    return {
        "safe_to_spend_pool": current_pool,
        "daily_safe_spend": current_daily,
        "weekly_safe_spend": metrics["weekly_safe_spend"],
        "weekend_safe_spend": metrics["weekend_safe_spend"],
        "days_remaining": days_left
    }


def check_upcoming_bills(user_id: int = 1) -> Dict[str, Any]:
    """
    Retrieves upcoming unpaid obligations and cleared history for the current cycle.
    """
    metrics = SafeSpendEngine.calculate_metrics(user_id)
    unpaid = metrics["unpaid_items"]
    paid = metrics["paid_items"]
    return {
        "unpaid_bills": unpaid,
        "unpaid_total": metrics["unpaid_obligations_total"],
        "unpaid_count": len(unpaid),
        "paid_bills": paid,
        "paid_total": sum(p.get("amount", 0.0) for p in paid),
        "paid_count": len(paid),
        "total_monthly_obligations": metrics["total_monthly_obligations"]
    }


def simulate_purchase(user_id: int = 1, price: float = 0.0, item_name: str = "Item", mode: str = "Upfront UPI / Card", tenure: int = 3) -> Dict[str, Any]:
    """
    Evaluates whether an item can be safely afforded without breaching the safety net.
    """
    return AffordabilitySimulator.evaluate_purchase(
        item_name=item_name,
        price=price,
        payment_mode=mode,
        emi_tenure_months=tenure,
        user_id=user_id
    )


def generate_savings_recommendation(user_id: int = 1) -> Dict[str, Any]:
    """
    Calculates personalized savings benchmarks and emergency fund adequacy.
    """
    metrics = SafeSpendEngine.calculate_metrics(user_id)
    income = float(metrics["profile"].get("monthly_income", 100000.0))
    obligations = metrics["total_monthly_obligations"]
    liquid = metrics["liquid_balance"]
    buffer = metrics["emergency_buffer"]

    # 50-30-20 rule adapted for urban Indian professionals
    recommended_savings = round(income * 0.20, 2)
    # Target emergency fund: 3 months of non-negotiable fixed obligations
    target_emergency_fund = round(obligations * 3.0, 2)
    emergency_gap = max(0.0, target_emergency_fund - liquid)

    active_sip = metrics["protected_savings_commitments"]
    surplus_pool = metrics["safe_to_spend"]

    return {
        "monthly_income": income,
        "recommended_monthly_savings": recommended_savings,
        "active_sip": active_sip,
        "target_emergency_fund": target_emergency_fund,
        "current_liquid_balance": liquid,
        "emergency_gap": emergency_gap,
        "surplus_safe_pool": surplus_pool,
        "emergency_buffer": buffer
    }


def analyze_category_spending(user_id: int = 1, keyword: str = "") -> Dict[str, Any]:
    """
    Analyzes live expenses for a specific category (e.g. Food, Groceries, Commute).
    """
    tx_df = db.get_transactions(user_id)
    if tx_df.empty:
        return {"category_keyword": keyword, "total_spent": 0.0, "count": 0, "share_pct": 0.0, "top_merchants": {}}

    tx_df_exp = tx_df[tx_df["type"] == "expense"].copy()
    matched = tx_df_exp[
        tx_df_exp["category"].str.contains(keyword, case=False, na=False) |
        tx_df_exp["merchant"].str.contains(keyword, case=False, na=False)
    ]

    total_spent_cat = float(matched["amount"].sum())
    total_spent_all = float(tx_df_exp["amount"].sum())
    share_pct = round((total_spent_cat / max(1.0, total_spent_all)) * 100, 1)

    top_merchants = matched.groupby("merchant")["amount"].sum().sort_values(ascending=False).head(4).to_dict()

    return {
        "category_keyword": keyword,
        "total_spent": total_spent_cat,
        "count": len(matched),
        "share_pct": share_pct,
        "total_spent_all": total_spent_all,
        "top_merchants": top_merchants
    }


# =============================================================
# NATURAL LANGUAGE PROCESSING & INTENT ROUTER
# =============================================================

class AIMoneyCoach:
    @staticmethod
    def get_financial_insights(user_id: int = 1) -> List[Dict[str, Any]]:
        """Existing proactive alerts for dashboard & coach header."""
        metrics = SafeSpendEngine.calculate_metrics(user_id)
        tx_df = db.get_transactions(user_id)
        insights = []

        if metrics["survival_mode"]:
            insights.append({
                "type": "danger",
                "badge": "🚨 Survival Mode Active",
                "title": "Immediate Discretionary Freeze Advised",
                "message": (
                    f"Your remaining safe pool is {format_inr(metrics['raw_pool'])}. "
                    f"Upcoming unpaid obligations ({format_inr(metrics['unpaid_obligations_total'])}) "
                    f"and emergency reserve ({format_inr(metrics['emergency_buffer'])}) exceed your liquid balance. "
                    "Pause all discretionary UPI payments (Swiggy, Zepto, Shopping) until your next salary credit."
                ),
                "action": "Activate Financial Survival Mode"
            })
            return insights

        daily_safe = metrics["daily_safe_spend"]
        days_left = metrics["days_remaining"]
        insights.append({
            "type": "success" if daily_safe > 1500 else "warning",
            "badge": "⚡ Safe-to-Spend Nudge",
            "title": f"You can safely spend {format_inr(daily_safe)} today",
            "message": (
                f"With {days_left} days left in this cycle, staying below {format_inr(daily_safe)}/day "
                f"guarantees you won't touch your {format_inr(metrics['emergency_buffer'])} emergency safety net "
                f"or miss upcoming obligations ({format_inr(metrics['unpaid_obligations_total'])})."
            ),
            "action": "Track today's spends"
        })

        if not tx_df.empty:
            food_and_qc = tx_df[tx_df["category"].str.contains("Food|Quick Commerce|Groceries", case=False, na=False)]
            if not food_and_qc.empty:
                qc_sum = food_and_qc["amount"].sum()
                qc_count = len(food_and_qc)
                if qc_sum > 3000:
                    insights.append({
                        "type": "purple",
                        "badge": "🍔 Micro-Leakage Alert",
                        "title": f"₹{qc_sum:,.0f} spent across {qc_count} Quick-Commerce & Food orders",
                        "message": (
                            "UPI convenience friction is low on 10-minute delivery apps (Blinkit/Zepto/Swiggy). "
                            "Aggregated micro-orders are taking up a substantial slice of your discretionary budget."
                        ),
                        "action": "Review Food & Grocery Orders"
                    })

        weekend_allowance = metrics["weekend_safe_spend"]
        insights.append({
            "type": "orange",
            "badge": "📅 Weekend Spending Guard",
            "title": f"Weekend Cap: {format_inr(weekend_allowance)} / day",
            "message": (
                f"Discretionary spending surges on Saturdays and Sundays. SafeSpend AI has dynamically "
                f"reserved an adjusted cap of {format_inr(weekend_allowance)} for your leisure activities."
            ),
            "action": "Plan Weekend"
        })

        return insights

    @classmethod
    def ask(cls, user_query: str, user_id: int = 1) -> str:
        """
        Main Conversational AI Entry Point.
        Interprets user prompt, calls specific Python financial tools,
        and generates an accurate, data-backed fintech response.
        """
        query = user_query.strip()
        query_lower = query.lower()

        # 1. INTENT: What-if spend today ("What happens if I spend ₹3,000 today?")
        if any(p in query_lower for p in ["what happens if", "what if i spend", "if i spend"]):
            amount = cls._extract_amount(query_lower)
            if amount and amount > 0:
                calc_res = calculate_safe_to_spend(user_id=user_id, what_if_spend=amount)
                return cls._respond_what_if_spend(calc_res)

        # 2. INTENT: Affordability ("Can I afford a ₹5,000 purchase?")
        if any(w in query_lower for w in ["afford", "can i buy", "should i buy", "purchase of"]):
            amount = cls._extract_amount(query_lower)
            if amount and amount > 0:
                is_emi = "emi" in query_lower
                tenure = 6 if "6" in query_lower else 3
                mode = f"No-Cost EMI ({tenure} Months)" if is_emi else "Upfront UPI / Card"
                item_name = cls._extract_item_name(query)
                sim_res = simulate_purchase(user_id=user_id, price=amount, item_name=item_name, mode=mode, tenure=tenure)
                return cls._respond_affordability(sim_res)

        # 3. INTENT: Weekly / Daily Allowance ("How much can I spend this week?")
        if any(w in query_lower for w in ["this week", "weekly", "spend today", "daily limit", "daily allowance", "safe to spend"]):
            calc_res = calculate_safe_to_spend(user_id=user_id)
            state = get_financial_state(user_id=user_id)
            return cls._respond_allowance(calc_res, state, query_lower)

        # 4. INTENT: Food / Dining Spending ("Am I spending too much on food?")
        if any(w in query_lower for w in ["food", "swiggy", "zomato", "dining", "eating out", "blinkit", "zepto", "groceries"]):
            food_res = analyze_category_spending(user_id=user_id, keyword="Food")
            qc_res = analyze_category_spending(user_id=user_id, keyword="Quick Commerce")
            return cls._respond_food_spending(food_res, qc_res)

        # 5. INTENT: Savings Recommendation ("How much should I save this month?")
        if any(w in query_lower for w in ["save", "saving", "savings", "how much should i save", "emergency fund", "invest", "sip"]):
            savings_res = generate_savings_recommendation(user_id=user_id)
            return cls._respond_savings(savings_res)

        # 6. INTENT: Upcoming Bills ("What bills are due?")
        if any(w in query_lower for w in ["bill", "due", "pending", "obligation", "commitment", "rent", "emi"]):
            bills_res = check_upcoming_bills(user_id=user_id)
            return cls._respond_bills(bills_res)

        # 7. INTENT: Financial Health Overview ("How am I doing financially?")
        if any(w in query_lower for w in ["health", "score", "status", "how am i doing", "overview", "summary"]):
            state = get_financial_state(user_id=user_id)
            return cls._respond_health_overview(state)

        # 8. GENERAL / FALLBACK ASSISTANT (with optional LLM enhancement)
        state = get_financial_state(user_id=user_id)
        llm_reply = cls._try_llm_completion(query, state)
        if llm_reply:
            return llm_reply
        return cls._respond_fallback(state, query)

    @classmethod
    def _try_llm_completion(cls, query: str, state: Dict[str, Any]) -> Optional[str]:
        """Optionally query an external LLM (OpenAI/Gemini) if API key is provided in environment."""
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            return None

        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            system_prompt = (
                f"You are SafeSpend AI, an intelligent personal finance coach tailored for Indian users.\n"
                f"Current Live Financial State:\n"
                f"- Liquid Bank Balance: ₹{state['liquid_balance']:,.0f}\n"
                f"- Active Safe-to-Spend Pool: ₹{state['safe_to_spend']:,.0f}\n"
                f"- Daily Safe Limit: ₹{state['daily_safe_spend']:,.0f} / day\n"
                f"- Days Remaining in Cycle: {state['days_remaining']} days\n"
                f"- Unpaid Fixed Bills: ₹{state['unpaid_obligations_total']:,.0f}\n"
                f"- Emergency Safety Buffer: ₹{state['emergency_buffer']:,.0f}\n"
                f"Respond helpfully using INR (₹) and Indian financial terminology (UPI, SIPs, EMIs)."
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                max_tokens=350,
                temperature=0.4
            )
            return response.choices[0].message.content
        except Exception:
            return None

    # ---------------------------------------------------------
    # Helper Entity Extractors
    # ---------------------------------------------------------
    @staticmethod
    def _extract_amount(text: str) -> Optional[float]:
        """Extract monetary amounts supporting ₹, commas, k, and lakh."""
        # Match ₹5,000 or 5000 or 5k or 1.5 lakh
        match_k = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]+)?)\s*k\b', text)
        if match_k:
            return float(match_k.group(1)) * 1000.0

        match_lakh = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:lakh|lac|l)\b', text)
        if match_lakh:
            return float(match_lakh.group(1)) * 100000.0

        match_num = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9]{1,3}(?:,[0-9]{2,3})+|[0-9]+)(?:\.[0-9]+)?', text)
        if match_num:
            raw_str = match_num.group(1).replace(",", "")
            try:
                return float(raw_str)
            except ValueError:
                pass
        return None

    @staticmethod
    def _extract_item_name(text: str) -> str:
        """Extract target purchase item name from user query."""
        patterns = [
            r'(?:afford|buy|purchase)\s+(?:a|an|the)?\s+([a-zA-Z0-9\s\-]+?)(?:\s+for|\s+of|\s+at|\s+worth|\?|$)',
            r'([a-zA-Z0-9\s\-]+?)\s+(?:worth|for)\s+(?:₹|rs\.?|[0-9])'
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                item = m.group(1).strip()
                # filter out generic terms
                if item.lower() not in ["it", "this", "purchase", "something", "a", "an"]:
                    return item.capitalize()
        return "Purchase Item"

    # ---------------------------------------------------------
    # Response Generators with Real Data
    # ---------------------------------------------------------
    @staticmethod
    def _respond_what_if_spend(res: Dict[str, Any]) -> str:
        spend = format_inr(res["what_if_spend"])
        curr_daily = format_inr(res["current_daily"])
        new_daily = format_inr(res["new_daily"])
        diff = format_inr(res["daily_reduction"])
        new_pool = format_inr(res["new_pool"])
        days = res["days_remaining"]

        if res["breached"]:
            deficit = format_inr(res["emergency_buffer_impact"])
            return (
                f"### 🚨 Spend Simulation Impact: {spend}\n\n"
                f"Spending **{spend}** today will **breach your safe pool by {deficit}** and cut directly into your emergency reserve!\n\n"
                f"- **Current Daily Safe Limit:** `{curr_daily} / day`\n"
                f"- **New Daily Safe Limit:** `₹0 / day` *(Survival Mode Triggered)*\n"
                f"- **Remaining Days in Cycle:** `{days} days`\n\n"
                f"💡 **Coach Advice:** I strongly advise against spending {spend} right now. Your liquid funds are committed to upcoming obligations and emergency safety."
            )

        return (
            f"### 🧪 Simulation Breakdown for {spend}\n\n"
            f"If you spend **{spend}** today, your daily safe-to-spend allowance for the remaining **{days} days** "
            f"will drop from **{curr_daily}** to **{new_daily}** (a reduction of **-{diff}/day**).\n\n"
            f"| Metric | Current | Post-Purchase |\n"
            f"| :--- | :--- | :--- |\n"
            f"| **Active Safe Pool** | `{format_inr(res['current_pool'])}` | `{new_pool}` |\n"
            f"| **Daily Safe Limit** | `{curr_daily}/day` | `{new_daily}/day` |\n"
            f"| **Days Remaining** | `{days} days` | `{days} days` |\n\n"
            f"💡 **Coach Advice:** Your new daily limit of `{new_daily}/day` remains positive. As long as your non-essential daily spends stay below `{new_daily}`, you are completely safe."
        )

    @staticmethod
    def _respond_affordability(res: Dict[str, Any]) -> str:
        price = format_inr(res["price"])
        item = res["item_name"]
        curr_daily = format_inr(res["current_daily"])
        new_daily = format_inr(res["new_daily"])
        verdict = res["verdict"]

        return (
            f"### {verdict}\n\n"
            f"**Analysis for {item} ({price}) via {res['mode']}:**\n\n"
            f"{res['advice']}\n\n"
            f"- **Current Daily Safe Limit:** `{curr_daily}/day`\n"
            f"- **Adjusted Daily Safe Limit:** `{new_daily}/day`\n"
            f"- **Remaining Safe Pool:** `{format_inr(res['safe_pool_remaining'])}`\n\n"
            f"📌 *Calculated using real-time liquid balance, pending EMIs/bills, and emergency buffer.*"
        )

    @staticmethod
    def _respond_allowance(calc_res: Dict[str, Any], state: Dict[str, Any], query: str) -> str:
        daily = format_inr(calc_res["daily_safe_spend"])
        weekly = format_inr(calc_res["weekly_safe_spend"])
        weekend = format_inr(calc_res["weekend_safe_spend"])
        pool = format_inr(calc_res["safe_to_spend_pool"])
        days = calc_res["days_remaining"]

        if "week" in query:
            return (
                f"### 📅 Weekly Spending Allowance: {weekly}\n\n"
                f"You can safely spend up to **{weekly} over the next 7 days** without encroaching on your emergency safety net.\n\n"
                f"- **Rolling 7-Day Cap:** `{weekly}`\n"
                f"- **Daily Safe Limit:** `{daily} / day`\n"
                f"- **Weekend Boosted Cap:** `{weekend} / day` (Sat/Sun)\n"
                f"- **Total Disposable Safe Pool:** `{pool}` (over `{days} days` remaining)\n\n"
                f"💡 **Tip:** If you spend below `{daily}` on weekdays, the surplus automatically pools into a higher weekend allowance!"
            )

        return (
            f"### ⚡ Today's Safe-to-Spend Limit: {daily}\n\n"
            f"Your guaranteed safe spending cap for today is **{daily}**.\n\n"
            f"- **Today's Limit:** `{daily} / day`\n"
            f"- **Weekend Cap:** `{weekend} / day`\n"
            f"- **7-Day Rolling Budget:** `{weekly}`\n"
            f"- **Days Until Next Salary:** `{days} days`\n\n"
            f"All your upcoming bills ({format_inr(state['unpaid_obligations_total'])}) and emergency buffer ({format_inr(state['emergency_buffer'])}) are already deducted and protected."
        )

    @staticmethod
    def _respond_food_spending(food_res: Dict[str, Any], qc_res: Dict[str, Any]) -> str:
        food_spent = food_res["total_spent"]
        food_count = food_res["count"]
        qc_spent = qc_res["total_spent"]
        qc_count = qc_res["count"]

        total_food_qc = food_spent + qc_spent
        total_orders = food_count + qc_count
        all_expenses = max(1.0, food_res["total_spent_all"])
        combined_pct = round((total_food_qc / all_expenses) * 100, 1)

        merchants = []
        for m, a in {**food_res["top_merchants"], **qc_res["top_merchants"]}.items():
            merchants.append(f"• **{m}:** {format_inr(a)}")
        merchant_str = "\n".join(merchants) if merchants else "• No merchant breakdown recorded yet."

        evaluation = (
            "🚨 **High Alert:** Food & quick commerce takes up >25% of your total expenses! UPI micro-transactions are silently leaking your safe-to-spend pool."
            if combined_pct > 25.0 else
            "🟢 **Healthy Control:** Your dining and quick-commerce spend is well within reasonable boundaries."
        )

        return (
            f"### 🍔 Food & Quick-Commerce Spending Diagnosis\n\n"
            f"You have spent **{format_inr(total_food_qc)}** across **{total_orders} orders** on food delivery, dining, and 10-minute groceries this month.\n\n"
            f"- **Food & Dining (Swiggy/Zomato):** `{format_inr(food_spent)}` ({food_count} transactions)\n"
            f"- **Quick Commerce (Blinkit/Zepto):** `{format_inr(qc_spent)}` ({qc_count} transactions)\n"
            f"- **Share of Total Monthly Spends:** `{combined_pct}%`\n\n"
            f"**Top Payees:**\n{merchant_str}\n\n"
            f"{evaluation}\n\n"
            f"💡 **Coach Advice:** Set a weekly ₹2,000 cap on delivery apps. Unlink UPI auto-pay from Swiggy/Blinkit and use a prepaid UPI wallet with a fixed recharge."
        )

    @staticmethod
    def _respond_savings(res: Dict[str, Any]) -> str:
        income = format_inr(res["monthly_income"])
        rec_savings = format_inr(res["recommended_monthly_savings"])
        active_sip = format_inr(res["active_sip"])
        target_ef = format_inr(res["target_emergency_fund"])
        liquid = format_inr(res["current_liquid_balance"])
        gap = format_inr(res["emergency_gap"])
        surplus = format_inr(res["surplus_safe_pool"])

        return (
            f"### 📈 Monthly Savings & Wealth Blueprint\n\n"
            f"Based on your monthly inhand income of **{income}**:\n\n"
            f"| Target | Recommended | Current Status |\n"
            f"| :--- | :--- | :--- |\n"
            f"| **Monthly Savings (20% Benchmark)** | `{rec_savings} / mo` | `{active_sip} in active SIPs` |\n"
            f"| **Emergency Fund (3x Commitments)** | `{target_ef}` | `{liquid} liquid cash` |\n"
            f"| **Surplus Safe-to-Spend Pool** | - | `{surplus}` |\n\n"
            f"**Action Plan:**\n"
            f"1. **Emergency Gap:** You are currently `{gap}` away from an optimal 3-month emergency cushion ({target_ef}).\n"
            f"2. **Wealth Discipline:** You have `{active_sip}` protected in systematic investments.\n"
            f"3. **Opportunity:** You can safely allocate an extra **₹3,000 - ₹5,000** this month toward liquid debt funds or gold."
        )

    @staticmethod
    def _respond_bills(res: Dict[str, Any]) -> str:
        unpaid = res["unpaid_bills"]
        unpaid_total = format_inr(res["unpaid_total"])
        unpaid_count = res["unpaid_count"]
        paid_count = res["paid_count"]

        if not unpaid:
            return (
                f"### 📋 Upcoming Bills: All Clear! 🟢\n\n"
                f"You have **zero pending obligations** for the rest of this cycle! All `{paid_count} recurring bills` have been settled.\n\n"
                f"Your full remaining balance is liberated for essentials and daily safe spend."
            )

        bill_items = []
        for b in unpaid:
            bill_items.append(f"• **{b['title']}:** `{format_inr(b['amount'])}` (Due on Day {b['due_day']}) — *{b['category']}*")
        bill_str = "\n".join(bill_items)

        return (
            f"### 📋 Pending Commitments: {unpaid_total}\n\n"
            f"You have **{unpaid_count} pending commitments** totaling **{unpaid_total}** due before your next salary:\n\n"
            f"{bill_str}\n\n"
            f"🔒 **Protected:** This {unpaid_total} is already ring-fenced and deducted from your Safe-to-Spend pool so you cannot accidentally spend it."
        )

    @staticmethod
    def _respond_health_overview(state: Dict[str, Any]) -> str:
        score = state["health_score"]
        status = state["status"]
        liquid = format_inr(state["liquid_balance"])
        safe_pool = format_inr(state["safe_to_spend"])
        daily = format_inr(state["daily_safe_spend"])
        bills = format_inr(state["unpaid_obligations_total"])
        buffer = format_inr(state["emergency_buffer"])
        days = state["days_remaining"]

        return (
            f"### 🛡️ Financial Health Score: {score}/100 ({status})\n\n"
            f"- **Liquid Bank Cash:** `{liquid}`\n"
            f"- **Active Safe-to-Spend Pool:** `{safe_pool}`\n"
            f"- **Daily Safe Allowance:** `{daily} / day` (for `{days} days`)\n"
            f"- **Ring-Fenced Unpaid Bills:** `{bills}`\n"
            f"- **Locked Emergency Cushion:** `{buffer}`\n\n"
            f"Your financial engine is operating smoothly. Keep your daily discretionary outlays below `{daily}` to preserve your safety floor."
        )

    @staticmethod
    def _respond_fallback(state: Dict[str, Any], query: str) -> str:
        daily = format_inr(state["daily_safe_spend"])
        pool = format_inr(state["safe_to_spend"])
        days = state["days_remaining"]

        return (
            f"I am your **SafeSpend AI Money Coach**, connected live to your Indian financial ledger.\n\n"
            f"Right now, you have **{pool}** in your safe pool with **{days} days remaining**, "
            f"giving you **{daily} / day** to spend safely.\n\n"
            f"**Here are questions you can ask me:**\n"
            f"• *\"Can I afford a ₹5,000 purchase?\"*\n"
            f"• *\"How much can I spend this week?\"*\n"
            f"• *\"Am I spending too much on food?\"*\n"
            f"• *\"How much should I save this month?\"*\n"
            f"• *\"What happens if I spend ₹3,000 today?\"*\n"
            f"• *\"What bills are due this month?\"*"
        )
