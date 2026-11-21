"""
Purchase Affordability Simulator Service.
Answers the core Indian consumer question: 'Can I afford this right now?'
Evaluates upfront UPI payment impact vs No-Cost EMI vs Standard Bank EMI (with interest, processing fee, and 18% GST).
"""
from typing import Dict, Any
from src.services.safe_spend import SafeSpendEngine
from src.utils.formatters import format_inr


class AffordabilitySimulator:
    @staticmethod
    def evaluate_purchase(
        item_name: str,
        price: float,
        payment_mode: str = "Upfront UPI / Card",
        emi_tenure_months: int = 3,
        annual_interest_rate: float = 0.0,
        processing_fee: float = 0.0,
        user_id: int = 1
    ) -> Dict[str, Any]:
        metrics = SafeSpendEngine.calculate_metrics(user_id)
        current_safe_pool = metrics["safe_to_spend"]
        days_remaining = metrics["days_remaining"]
        current_daily_spend = metrics["daily_safe_spend"]

        if price <= 0:
            return {"error": "Invalid price"}

        if payment_mode == "Upfront UPI / Card":
            post_purchase_pool = current_safe_pool - price
            post_daily_spend = max(0.0, round(post_purchase_pool / days_remaining, 2)) if post_purchase_pool > 0 else 0.0
            daily_drop = current_daily_spend - post_daily_spend

            if post_purchase_pool > (metrics["emergency_buffer"] * 0.5):
                verdict = "SAFE TO BUY 🟢"
                verdict_color = "#00F59B"
                advice = (
                    f"You have ample cushion. Buying {item_name} for {format_inr(price)} upfront "
                    f"reduces your daily safe-to-spend from {format_inr(current_daily_spend)} to {format_inr(post_daily_spend)} "
                    f"(-{format_inr(daily_drop)}/day)."
                )
            elif post_purchase_pool > 0:
                verdict = "CAUTION REQUIRED 🟡"
                verdict_color = "#F97316"
                advice = (
                    f"Affordable, but your daily spending allowance will shrink drastically to {format_inr(post_daily_spend)}/day. "
                    "Avoid other discretionary spends for the rest of this cycle."
                )
            else:
                verdict = "NOT RECOMMENDED 🔴"
                verdict_color = "#EF4444"
                deficit = abs(post_purchase_pool)
                advice = (
                    f"Buying {item_name} upfront will breach your safe spending pool by {format_inr(deficit)} "
                    f"and eat into your emergency safety buffer ({format_inr(metrics['emergency_buffer'])}). "
                    "Consider deferring to next salary cycle."
                )

            return {
                "item_name": item_name,
                "price": price,
                "mode": payment_mode,
                "verdict": verdict,
                "verdict_color": verdict_color,
                "advice": advice,
                "current_daily": current_daily_spend,
                "new_daily": post_daily_spend,
                "safe_pool_remaining": max(0.0, post_purchase_pool),
                "breaches_buffer": post_purchase_pool < 0,
                "monthly_emi": 0.0,
                "total_extra_cost": 0.0,
                "is_emi": False
            }

        else:
            # EMI Mode (No-Cost vs Standard with Interest & 18% GST)
            n = max(1, emi_tenure_months)
            p = price

            if annual_interest_rate > 0:
                monthly_rate = (annual_interest_rate / 100.0) / 12.0
                monthly_emi = round(
                    p * monthly_rate * ((1 + monthly_rate) ** n) / (((1 + monthly_rate) ** n) - 1), 2
                )
                total_interest = round((monthly_emi * n) - p, 2)
                gst_on_interest = round(total_interest * 0.18, 2)
                gst_on_fee = round(processing_fee * 0.18, 2)
                total_extra_cost = round(total_interest + gst_on_interest + processing_fee + gst_on_fee, 2)
                effective_monthly_commitment = round(monthly_emi + (gst_on_interest / n), 2)
            else:
                monthly_emi = round(p / n, 2)
                total_interest = 0.0
                gst_on_interest = 0.0
                gst_on_fee = round(processing_fee * 0.18, 2)
                total_extra_cost = round(processing_fee + gst_on_fee, 2)
                effective_monthly_commitment = monthly_emi

            post_purchase_pool = current_safe_pool - effective_monthly_commitment
            post_daily_spend = max(0.0, round(post_purchase_pool / days_remaining, 2))

            if post_purchase_pool > 0:
                verdict = "AFFORDABLE ON EMI 🟣"
                verdict_color = "#8B5CF6"
                advice = (
                    f"Splitting into {n} monthly EMIs of {format_inr(effective_monthly_commitment)} preserves your immediate cash flow. "
                    f"Your daily budget adjusts to {format_inr(post_daily_spend)}/day. "
                    f"{'Total interest + 18% GST: ' + format_inr(total_extra_cost) if total_extra_cost > 0 else 'No-Cost EMI (₹0 extra interest)'}."
                )
            else:
                verdict = "EMI OVERLOAD 🔴"
                verdict_color = "#EF4444"
                advice = (
                    f"Even an EMI of {format_inr(effective_monthly_commitment)}/month stretches your commitments too thin. "
                    "Clear existing obligations before taking on new debt."
                )

            return {
                "item_name": item_name,
                "price": price,
                "mode": f"EMI ({n} Months)",
                "monthly_emi": effective_monthly_commitment,
                "base_emi": monthly_emi,
                "total_interest": total_interest,
                "total_extra_cost": total_extra_cost,
                "is_emi": True,
                "verdict": verdict,
                "verdict_color": verdict_color,
                "advice": advice,
                "current_daily": current_daily_spend,
                "new_daily": post_daily_spend,
                "safe_pool_remaining": max(0.0, post_purchase_pool),
                "breaches_buffer": post_purchase_pool < 0
            }
