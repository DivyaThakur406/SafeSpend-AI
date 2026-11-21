"""
Indian Bank SMS and Statement Parser Service.
Parses instant debit/credit alerts from HDFC, SBI, ICICI, Axis, GPay, PhonePe, and Paytm.
"""
import re
from datetime import datetime, date
from typing import Dict, Any, List, Optional
import pandas as pd
from dateutil import parser as date_parser

from src.config import EXPENSE_CATEGORIES, INCOME_CATEGORIES, UPI_APPS


KNOWN_MERCHANTS_CATEGORY = {
    "swiggy": ("Food & Dining (Swiggy/Zomato)", False),
    "zomato": ("Food & Dining (Swiggy/Zomato)", False),
    "blue tokai": ("Food & Dining (Swiggy/Zomato)", False),
    "starbucks": ("Food & Dining (Swiggy/Zomato)", False),
    "chai point": ("Food & Dining (Swiggy/Zomato)", False),
    "mcdonalds": ("Food & Dining (Swiggy/Zomato)", False),
    "blinkit": ("Quick Commerce & Groceries (Zepto/Blinkit)", True),
    "zepto": ("Quick Commerce & Groceries (Zepto/Blinkit)", True),
    "instamart": ("Quick Commerce & Groceries (Zepto/Blinkit)", True),
    "bigbasket": ("Quick Commerce & Groceries (Zepto/Blinkit)", True),
    "uber": ("Commute & Fuel (Uber/Ola/Metro)", True),
    "ola": ("Commute & Fuel (Uber/Ola/Metro)", True),
    "rapido": ("Commute & Fuel (Uber/Ola/Metro)", True),
    "petrol": ("Commute & Fuel (Uber/Ola/Metro)", True),
    "indian oil": ("Commute & Fuel (Uber/Ola/Metro)", True),
    "shell": ("Commute & Fuel (Uber/Ola/Metro)", True),
    "hpcl": ("Commute & Fuel (Uber/Ola/Metro)", True),
    "bpcl": ("Commute & Fuel (Uber/Ola/Metro)", True),
    "amazon": ("Shopping & E-Commerce", False),
    "flipkart": ("Shopping & E-Commerce", False),
    "myntra": ("Shopping & E-Commerce", False),
    "zara": ("Shopping & E-Commerce", False),
    "netflix": ("Entertainment & OTT", False),
    "spotify": ("Entertainment & OTT", False),
    "hotstar": ("Entertainment & OTT", False),
    "prime": ("Entertainment & OTT", False),
    "bookmyshow": ("Entertainment & OTT", False),
    "apollo": ("Health, Medical & Gym", True),
    "pharmacy": ("Health, Medical & Gym", True),
    "cult.fit": ("Health, Medical & Gym", True),
    "1mg": ("Health, Medical & Gym", True),
    "airtel": ("Bills & Utilities (Electricity/WiFi)", True),
    "jio": ("Bills & Utilities (Electricity/WiFi)", True),
    "bescom": ("Bills & Utilities (Electricity/WiFi)", True),
    "rent": ("Rent & Housing", True),
    "salary": ("Salary / Monthly Staging", True),
}


def parse_indian_bank_sms(sms_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse an Indian bank SMS / UPI notification into a normalized transaction dict.
    Example: 'Sent Rs. 450.00 from HDFC Bank to Blue Tokai via UPI on 21-11-2026. Ref 12345'
    """
    if not sms_text or len(sms_text.strip()) < 10:
        return None

    clean_text = sms_text.strip()
    lower_text = clean_text.lower()

    # 1. Determine Type: Expense vs Income
    if any(k in lower_text for k in ["credited", "received", "refund", "salary", "cashback"]):
        tx_type = "income"
    elif any(k in lower_text for k in ["debited", "sent", "paid", "spent", "withdrawn"]):
        tx_type = "expense"
    else:
        tx_type = "expense"

    # 2. Extract Amount
    # Matches Rs. 450.00 or INR 1,240 or Rs 820
    amt_match = re.search(r'(?:rs\.?|inr|₹)\s*([0-9]{1,3}(?:,[0-9]{2,3})+|[0-9]+(?:\.[0-9]+)?)', clean_text, re.IGNORECASE)
    if not amt_match:
        # Fallback: look for debited by 450 or sent 450
        amt_match = re.search(r'(?:debited(?:\s+by)?|sent|paid)\s+([0-9]+(?:\.[0-9]+)?)', clean_text, re.IGNORECASE)
    
    if not amt_match:
        return None

    amount = float(amt_match.group(1).replace(",", ""))

    # 3. Detect Merchant / Payee
    merchant = "Unknown Payee"
    merchant_match = re.search(r'(?:to|towards|at|transfer\s+to|vpa)\s+([A-Za-z0-9\s\.\-_&]+?)(?:\s+via|\s+on|\s+ref|\s+avail|\.|$)', clean_text, re.IGNORECASE)
    if merchant_match:
        cand = merchant_match.group(1).strip()
        if len(cand) > 1 and not any(w in cand.lower() for w in ["your", "account", "a/c", "upi"]):
            merchant = cand.title()

    # If generic, test known merchants
    for k in KNOWN_MERCHANTS_CATEGORY:
        if k in lower_text:
            merchant = k.title()
            break

    # 4. Detect Category & Essential flag
    category = "Miscellaneous / Other" if tx_type == "expense" else "Salary / Monthly Staging"
    is_essential = 0

    for k, (cat, ess) in KNOWN_MERCHANTS_CATEGORY.items():
        if k in lower_text or k in merchant.lower():
            category = cat
            is_essential = 1 if ess else 0
            break

    # 5. Detect UPI Channel
    upi_app = "Google Pay"
    if "phonepe" in lower_text:
        upi_app = "PhonePe"
    elif "paytm" in lower_text:
        upi_app = "Paytm"
    elif "cred" in lower_text:
        upi_app = "CRED UPI"
    elif "bhim" in lower_text:
        upi_app = "BHIM"
    elif "amazon" in lower_text:
        upi_app = "Amazon Pay"
    elif any(b in lower_text for b in ["hdfc", "sbi", "icici", "axis", "kotak", "imps", "neft"]):
        upi_app = "Bank App (IMPS/NEFT)"

    # 6. Extract Date
    tx_date = str(date.today())
    date_match = re.search(r'\b([0-9]{1,2}[-/\.][0-9]{1,2}[-/\.][0-9]{2,4}|[0-9]{1,2}[-\s][A-Za-z]{3}[-\s][0-9]{2,4})\b', clean_text)
    if date_match:
        try:
            parsed = date_parser.parse(date_match.group(1), dayfirst=True)
            tx_date = parsed.strftime("%Y-%m-%d")
        except Exception:
            pass

    return {
        "date": tx_date,
        "amount": amount,
        "type": tx_type,
        "category": category,
        "upi_app": upi_app,
        "merchant": merchant,
        "note": f"Parsed from SMS: {clean_text[:60]}...",
        "is_essential": is_essential
    }


def parse_bank_statement_csv(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Parse a generic Indian Bank Statement CSV (HDFC, ICICI, SBI, etc.)
    """
    parsed_transactions = []
    col_map = {c.lower().strip(): c for c in df.columns}

    # Find Date column
    date_col = next((col_map[k] for k in ["date", "txn date", "transaction date", "value date"] if k in col_map), None)
    # Find Narration / Description column
    desc_col = next((col_map[k] for k in ["narration", "description", "particulars", "remarks", "details"] if k in col_map), None)
    # Find Debit / Credit columns
    debit_col = next((col_map[k] for k in ["debit", "withdrawal", "dr", "debit amount"] if k in col_map), None)
    credit_col = next((col_map[k] for k in ["credit", "deposit", "cr", "credit amount"] if k in col_map), None)
    amount_col = next((col_map[k] for k in ["amount", "txn amount"] if k in col_map), None)

    for _, row in df.iterrows():
        try:
            # Determine Date
            raw_date = row[date_col] if date_col else str(date.today())
            try:
                tx_date = date_parser.parse(str(raw_date), dayfirst=True).strftime("%Y-%m-%d")
            except Exception:
                tx_date = str(date.today())

            # Determine Amount and Type
            amt = 0.0
            tx_type = "expense"

            if debit_col and pd.notna(row[debit_col]) and float(str(row[debit_col]).replace(",", "") or 0) > 0:
                amt = float(str(row[debit_col]).replace(",", ""))
                tx_type = "expense"
            elif credit_col and pd.notna(row[credit_col]) and float(str(row[credit_col]).replace(",", "") or 0) > 0:
                amt = float(str(row[credit_col]).replace(",", ""))
                tx_type = "income"
            elif amount_col and pd.notna(row[amount_col]):
                amt_val = float(str(row[amount_col]).replace(",", ""))
                amt = abs(amt_val)
                tx_type = "expense" if amt_val < 0 else "income"
            else:
                continue

            if amt <= 0:
                continue

            # Narration
            raw_desc = str(row[desc_col]) if desc_col and pd.notna(row[desc_col]) else "Bank Transaction"
            lower_desc = raw_desc.lower()

            # Categorize
            category = "Miscellaneous / Other" if tx_type == "expense" else "Salary / Monthly Staging"
            is_essential = 0
            merchant = raw_desc[:30]

            for k, (cat, ess) in KNOWN_MERCHANTS_CATEGORY.items():
                if k in lower_desc:
                    category = cat
                    is_essential = 1 if ess else 0
                    merchant = k.title()
                    break

            # Channel
            channel = "Bank App (IMPS/NEFT)"
            for app in UPI_APPS:
                if app.lower() in lower_desc:
                    channel = app
                    break

            parsed_transactions.append({
                "date": tx_date,
                "amount": amt,
                "type": tx_type,
                "category": category,
                "upi_app": channel,
                "merchant": merchant,
                "note": f"CSV Import: {raw_desc[:40]}",
                "is_essential": is_essential
            })
        except Exception:
            continue

    return parsed_transactions
