# SafeSpend AI 🇮🇳
### Intelligent Personal Finance Companion for Indian Users

SafeSpend AI is a production-grade personal finance engine built specifically for the realities of the Indian fintech landscape: instant UPI micro-transactions, salary credit cycles, variable household essentials, and non-negotiable obligations.

Unlike traditional budgeting apps that enforce rigid, static monthly caps, **SafeSpend AI dynamically calculates your real-time daily disposable allowance** by actively ring-fencing upcoming fixed commitments (Rent, EMI, SIP, WiFi, Maid), remaining essential living expenses, protected savings targets, and an emergency safety buffer.

---

## 🎨 Design Philosophy
Engineered with a **bold, modern fintech visual identity**:
- **Canvas / Navy**: `#0A0E1A` deep space navy background and `#121A2D` card containers
- **Vibrant Emerald Green**: `#00F59B` (representing safe liquidity, positive cashflow, and active safe runway)
- **Electric Purple**: `#8B5CF6` (AI coaching, smart insights, savings goals, and long-term wealth)
- **Radiant Orange / Coral**: `#F97316` (UPI transactions, cautionary thresholds, and upcoming commitments)
- **Circuit Red**: `#EF4444` (Financial Survival Mode & emergency deficit alerts)

---

## 🏗️ Project Architecture

```
SafeSpend-AI/
├── .streamlit/
│   ├── config.toml           # Streamlit theme, headless mode & port configuration
│   └── credentials.toml      # Local sandbox credentials configuration
├── data/
│   └── safespend.db          # Auto-seeded SQLite database
├── src/
│   ├── __init__.py
│   ├── config.py             # Indian categories, UPI apps, and constants
│   ├── database/
│   │   ├── __init__.py
│   │   ├── schema.py         # SQLite DDL tables (user_profile, obligations, transactions, savings_goals)
│   │   └── db_manager.py     # SQLite connection, schema migrations, CRUD helpers, auto-seeding
│   ├── services/
│   │   ├── __init__.py
│   │   ├── safe_spend.py     # Dynamic Safe-to-Spend 5-term calculation engine
│   │   ├── transactions.py   # Transaction analysis & category aggregations
│   │   ├── coach.py          # Conversational AI Money Coach & 5 financial tools
│   │   ├── affordability.py  # Purchase Affordability Simulator (Upfront, No-Cost & Standard EMI + GST)
│   │   └── sms_parser.py     # Indian Bank SMS & Statement CSV Ingestion Engine
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── styles.py         # Custom CSS fintech styling, chat bubbles & telemetry cards
│   │   ├── components.py     # Reusable UI widgets, cards, and KPI displays
│   │   └── charts.py         # Plotly dark fintech visualizations
│   └── utils/
│       ├── __init__.py
│       └── formatters.py     # Indian currency (Lakhs/Crores, ₹), date formatters & XSS sanitizer
├── app.py                    # Main Streamlit application
├── test_e2e_runner.py        # Comprehensive 8-stage automated test suite
├── requirements.txt          # Python dependencies
└── README.md                 # Complete documentation & setup guide
```

---

## ⚡ Core Functional Features

### 1. Dynamic Safe-to-Spend Calculator Engine
Implements the exact 5-term mathematical formula without double-counting expenses already deducted from balance:

$$\text{Safe Pool} = \text{Liquid Balance} - \text{Upcoming Unpaid Obligations} - \text{Remaining Essential Expenses} - \text{Protected Savings Commitments} - \text{Emergency Buffer}$$

$$\text{Safe-to-Spend} = \max(0, \text{Safe Pool})$$

$$\text{Daily Safe-to-Spend} = \frac{\text{Safe-to-Spend}}{\text{Days Remaining in Cycle}}$$

- **Non-Double-Counting**: Variable essentials already spent decrease both liquid balance and remaining essential obligation in lockstep.
- **Cycle Reset**: Interactive "Start Fresh Monthly Cycle" button resets all obligations to pending when salary is credited.
- **Weekend Surge Weighting**: Automatically balances weekday vs weekend (+35%) spending velocity.
- **Interactive What-If Slider**: Real-time evaluation of how an immediate impulse purchase affects your daily allowance.

### 2. Ring-Fenced Fixed Commitments & Savings Goals Tracker
- **Settlement Actions**:
  - `Mark as Settled`: Marks bill as paid if already debited outside the app (preserves bank balance).
  - `Pay & Deduct from Bank`: Immediately marks bill as paid AND debits liquid bank balance.
  - `Revert to Pending`: Restores obligation to pending status.
- **Savings Goals Tracker**: Track progress toward custom targets (Goa trip, emergency fund, gadgets) with instant contributions that update liquid balance.

### 3. Indian UPI Transaction Ledger & Automated Ingestion
- **Manual Logging**: Log expenses and income across GPay, PhonePe, Paytm, CRED, and BHIM.
- **Instant Bank SMS Parser**: Paste raw debit/credit SMS alerts from HDFC, SBI, ICICI, Axis, or UPI apps to extract amounts, merchants, channels, and categories automatically.
- **Bank Statement CSV Importer**: Batch-import bank statement CSV files directly into the ledger with balance adjustments.
- **CSV Ledger Export**: One-click download of the entire enriched transaction ledger.

### 4. Conversational AI Money Coach with Financial Tools
Connects directly to the live SQLite ledger and executes Python financial tools:
- `get_financial_state()`: Real-time telemetry, liquid balance, and health score.
- `calculate_safe_to_spend(what_if_spend)`: Live daily allowance and what-if calculations.
- `check_upcoming_bills()`: Pending obligations and due dates.
- `simulate_purchase(price, item, mode, tenure)`: Instant Go/Caution/No-Go affordability checks.
- `generate_savings_recommendation()`: 50-30-20 rule adapted for India and emergency fund adequacy checks.
- `analyze_category_spending(keyword)`: Diagnoses food, dining, and 10-minute quick commerce (Blinkit/Zepto/Swiggy) micro-leakages.

> **Offline-First Resilience**: If an external LLM API key (`OPENAI_API_KEY`) is not present, the coach uses a deterministic rule-based natural language router that accurately parses queries and executes live Python calculations without mock or placeholder data.

### 5. Purchase Affordability Simulator with Indian Banking EMI & GST
Answers: *"Can I afford this right now?"*
- **Upfront UPI/Card**: Evaluates the post-purchase daily safe limit drop.
- **No-Cost EMI**: Calculates zero-interest monthly outflow.
- **Standard Bank EMI**: Uses exact reducing balance amortization formulas with **18% GST** on interest and processing fees as mandated by Indian banking regulations.
- **One-Click Commitment Lock**: Convert any simulated EMI directly into an active ring-fenced monthly obligation.

### 6. Financial Survival Mode & Circuit Breaker
- Automatically engages when safe liquidity reaches ₹0 or dips below emergency buffer.
- Features a **Manual Emergency Circuit Breaker** toggle in session state that locks daily safe spending to ₹0 across all modules.
- Includes an **Emergency Freeze** button to clamp essential expenses to a bare-minimum ₹5,000 staples budget.

---

## 🚀 How to Run the Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Automated Regression Test Suite
```bash
python test_e2e_runner.py
```
*Executes all 8 test suites covering database CRUD, formula mathematics, EMI/GST amortization, SMS/CSV parsing, and AI Money Coach tools.*

### 3. Launch the Streamlit Application
```bash
streamlit run app.py
```

The application will launch in your browser at `http://localhost:8501`. On the first run, it automatically creates `data/safespend.db` and seeds realistic Indian financial profile, obligations, savings goals, and UPI transaction history.
