"""
Configuration and constants for SafeSpend AI.
Tailored for Indian personal finance nuances (UPI, INR, salary cycles).
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "safespend.db"

# Fintech Color Palette
COLORS = {
    "bg_navy_deep": "#0A0E1A",
    "bg_card": "#121A2D",
    "bg_card_hover": "#1A253D",
    "border_subtle": "#1E293B",
    "border_glow": "rgba(0, 245, 155, 0.25)",
    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    
    # Accent Colors
    "accent_green": "#00F59B",      # Safe / Positive / In-budget
    "accent_green_glow": "rgba(0, 245, 155, 0.15)",
    "accent_purple": "#8B5CF6",     # AI Intelligence / Premium
    "accent_purple_glow": "rgba(139, 92, 246, 0.15)",
    "accent_orange": "#F97316",     # Caution / UPI Tag / Attention
    "accent_orange_glow": "rgba(249, 115, 22, 0.15)",
    "accent_red": "#EF4444",        # Alert / Critical / Survival Mode
    "accent_cyan": "#06B6D4",       # Analytics / Cashflow
}

# Indian UPI Ecosystem Apps
UPI_APPS = [
    "Google Pay",
    "PhonePe",
    "Paytm",
    "CRED UPI",
    "BHIM",
    "Amazon Pay",
    "Bank App (IMPS/NEFT)",
    "Card / Cash"
]

# Indian Expense Categories
EXPENSE_CATEGORIES = [
    "Food & Dining (Swiggy/Zomato)",
    "Quick Commerce & Groceries (Zepto/Blinkit)",
    "Rent & Housing",
    "EMI & Debt Repayment",
    "Investments & Mutual Funds (SIP)",
    "Bills & Utilities (Electricity/WiFi)",
    "Commute & Fuel (Uber/Ola/Metro)",
    "Shopping & E-Commerce",
    "Entertainment & OTT",
    "Health, Medical & Gym",
    "Domestic Help & Maintenance",
    "Miscellaneous / Other"
]

INCOME_CATEGORIES = [
    "Salary / Monthly Staging",
    "Freelance / Consulting",
    "Investment Returns / Dividends",
    "Rental Income",
    "Cashback & Rewards",
    "Other Inflow"
]

# Safe-to-Spend Thresholds
ALERT_THRESHOLDS = {
    "healthy_ratio": 0.35,      # >35% of daily budget remaining is great
    "caution_ratio": 0.15,      # 15%-35% remaining
    "danger_ratio": 0.05,       # <15% triggers warning
    "survival_mode_ratio": 0.0  # Zero or negative triggers Financial Survival Mode
}
