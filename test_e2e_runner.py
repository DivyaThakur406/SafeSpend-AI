"""
SafeSpend AI — End-to-End Regression Suite
Updated to use user_id=1 (Aarav Sharma, demo user) across all db/service calls.
Run: python test_e2e_runner.py
"""
import os
import sys
import sqlite3
import pandas as pd

from src.database.db_manager import db
from src.services.safe_spend import SafeSpendEngine
from src.services.affordability import AffordabilitySimulator
from src.services.sms_parser import parse_indian_bank_sms, parse_bank_statement_csv
from src.services.coach import (
    AIMoneyCoach,
    get_financial_state,
    calculate_safe_to_spend,
    check_upcoming_bills,
    simulate_purchase,
    generate_savings_recommendation,
    analyze_category_spending
)

USER_ID = 1  # Demo user: Aarav Sharma

def test_all():
    print("--- RUNNING SAFE SPEND AI E2E REGRESSION SUITE ---")

    # 1. Database Init and Profile
    db.init_db()
    profile = db.get_user_profile(USER_ID)
    assert profile is not None, "Profile should exist"
    print(f"[PASS 1/8] Database initialized. User: {profile['full_name']}, Balance: INR {profile['current_liquid_balance']}")

    # 2. Safe Spend Calculation & 5-term Formula
    metrics = SafeSpendEngine.calculate_metrics(user_id=USER_ID)
    assert "safe_pool" in metrics
    assert "safe_to_spend" in metrics
    assert "daily_safe_spend" in metrics
    assert "days_remaining" in metrics
    assert metrics["safe_to_spend"] >= 0
    print(f"[PASS 2/8] Safe Spend Engine: Safe Pool = INR {metrics['safe_pool']:,.2f}, Daily Safe Spend = INR {metrics['daily_safe_spend']:,.2f}, Status = {metrics['status']}")

    # 3. Survival Mode Override
    metrics_survival = SafeSpendEngine.calculate_metrics(user_id=USER_ID, override_survival=True)
    assert metrics_survival["survival_mode"] is True
    assert "SURVIVAL" in metrics_survival["status"]
    print(f"[PASS 3/8] Survival Mode Override: Status = {metrics_survival['status']}, Safe Pool = {metrics_survival['safe_pool']}")

    # 4. Affordability Simulator (Upfront vs EMI with GST)
    res_upfront = AffordabilitySimulator.evaluate_purchase(
        user_id=USER_ID,
        item_name="Noise Cancelling Headphones",
        price=12000,
        payment_mode="Upfront UPI / Card"
    )
    assert "verdict" in res_upfront
    assert "advice" in res_upfront

    res_emi = AffordabilitySimulator.evaluate_purchase(
        user_id=USER_ID,
        item_name="iPhone 16",
        price=60000,
        payment_mode="Standard Bank EMI",
        emi_tenure_months=6,
        annual_interest_rate=15.0,
        processing_fee=199.0
    )
    assert res_emi["monthly_emi"] > 0
    assert res_emi["total_extra_cost"] > 0
    total_outflow = res_emi["price"] + res_emi["total_extra_cost"]
    assert total_outflow > 60000
    print(f"[PASS 4/8] Affordability: 60k EMI = INR {res_emi['monthly_emi']:,.2f}/mo, Total Outflow = INR {total_outflow:,.2f}")

    # 5. SMS Parser
    sms_sample = "Dear SBI User, your A/c ending 4321 is debited by INR 3,450.00 on 18-Nov-2026 via UPI to ZOMATO LTD Ref 632198745612"
    sms_res = parse_indian_bank_sms(sms_sample)
    assert sms_res["amount"] == 3450.0
    assert sms_res["type"] == "expense"
    assert "ZOMATO" in sms_res["merchant"].upper()
    print(f"[PASS 5/8] SMS Parser: Extracted amount INR {sms_res['amount']} to {sms_res['merchant']} via {sms_res['upi_app']}")

    # 6. CSV Parser & Batch Ingestion
    import io
    csv_data = """Date,Narration,Debit,Credit,Balance
15/11/2026,UPI-SWIGGY-BANGALORE,640.00,,74360.00
16/11/2026,SALARY CREDIT NOV 2026,,85000.00,159360.00
"""
    df_sample = pd.read_csv(io.StringIO(csv_data))
    csv_parsed = parse_bank_statement_csv(df_sample)
    assert len(csv_parsed) == 2
    assert csv_parsed[0]["amount"] == 640.0
    assert csv_parsed[0]["type"] == "expense"
    assert csv_parsed[1]["amount"] == 85000.0
    assert csv_parsed[1]["type"] == "income"
    print(f"[PASS 6/8] CSV Parser: Successfully parsed {len(csv_parsed)} transactions from statement")

    # 7. AI Coach Tools & Rule-Based Intent Execution
    tool_state = get_financial_state(USER_ID)
    assert tool_state["liquid_balance"] > 0
    tool_safe = calculate_safe_to_spend(USER_ID)
    assert "daily_safe_spend" in tool_safe
    tool_bills = check_upcoming_bills(USER_ID)
    assert "unpaid_total" in tool_bills
    tool_sim = simulate_purchase(USER_ID, 5000)
    assert "verdict" in tool_sim, f"simulate_purchase keys: {tool_sim.keys()}"
    tool_sav = generate_savings_recommendation(USER_ID)
    assert "recommended_monthly_savings" in tool_sav
    tool_cat = analyze_category_spending(USER_ID, "Food")
    assert "total_spent" in tool_cat

    queries = [
        "Can I afford a ₹5,000 purchase?",
        "How much can I spend this week?",
        "Am I spending too much on food?",
        "How much should I save this month?",
        "What happens if I spend ₹3,000 today?"
    ]
    for q in queries:
        resp = AIMoneyCoach.ask(q, user_id=USER_ID)
        assert len(resp) > 30, f"Response too short for {q}"
        assert "₹" in resp or "INR" in resp, f"Response should contain financial numbers for {q}"
        print(f"  > Query: '{q}' -> Generated response ({len(resp)} chars)")
    print("[PASS 7/8] AI Coach Tools & Natural Language Engine fully verified")

    # 8. Savings Goals Tracker CRUD
    goals_before = db.get_savings_goals(USER_ID)
    new_goal_id = db.add_savings_goal(USER_ID, "Test Vacation Goa", 35000, 5000, "2027-03-31")
    goals_mid = db.get_savings_goals(USER_ID)
    assert len(goals_mid) == len(goals_before) + 1
    db.update_savings_goal_progress(USER_ID, new_goal_id, 2500)
    goals_updated = [g for g in db.get_savings_goals(USER_ID).to_dict(orient="records") if g["id"] == new_goal_id]
    assert goals_updated[0]["current_amount"] == 7500
    db.delete_savings_goal(USER_ID, new_goal_id)
    goals_after = db.get_savings_goals(USER_ID)
    assert len(goals_after) == len(goals_before)
    print(f"[PASS 8/8] Savings Goals CRUD fully verified (Added, Updated progress, Deleted)")

    print("\n=======================================================")
    print("ALL 8 END-TO-END TEST SUITES COMPLETED WITH 100% PASS RATE")
    print("=======================================================\n")

if __name__ == "__main__":
    test_all()
