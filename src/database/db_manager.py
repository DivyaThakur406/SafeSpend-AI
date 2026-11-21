"""
Database Manager for SafeSpend AI.
Handles SQLite operations, connections, user authentication, and strict user-level data isolation.
"""
import sqlite3
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd

from src.config import DB_PATH
from src.database.schema import CREATE_TABLES_SQL
from src.utils.security import hash_password, verify_password


class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = str(db_path)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialise tables and perform non-destructive schema migrations."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(CREATE_TABLES_SQL)

            # --- MIGRATION CHECKS ---
            # 1. Add user_id column to obligations if missing
            cursor.execute("PRAGMA table_info(obligations)")
            ob_cols = [row["name"] for row in cursor.fetchall()]
            if "user_id" not in ob_cols:
                cursor.execute("ALTER TABLE obligations ADD COLUMN user_id INTEGER DEFAULT 1")

            # 2. Add user_id column to transactions if missing
            cursor.execute("PRAGMA table_info(transactions)")
            tx_cols = [row["name"] for row in cursor.fetchall()]
            if "user_id" not in tx_cols:
                cursor.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER DEFAULT 1")

            # 3. Add user_id column to savings_goals if missing
            cursor.execute("PRAGMA table_info(savings_goals)")
            sg_cols = [row["name"] for row in cursor.fetchall()]
            if "user_id" not in sg_cols:
                cursor.execute("ALTER TABLE savings_goals ADD COLUMN user_id INTEGER DEFAULT 1")

            # 4. Ensure default demo user (Aarav Sharma) exists in users table
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            if user_count == 0:
                demo_hash = hash_password("SafeSpend@123")
                cursor.execute("""
                    INSERT INTO users (id, full_name, email, password_hash, account_status)
                    VALUES (1, 'Aarav Sharma', 'aarav@safespend.ai', ?, 'active')
                """, (demo_hash,))

            # 5. Populate user_profiles table from old user_profile or default
            cursor.execute("SELECT COUNT(*) FROM user_profiles WHERE user_id = 1")
            profile_count = cursor.fetchone()[0]
            if profile_count == 0:
                # Check if legacy user_profile exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profile'")
                legacy_exists = cursor.fetchone()
                if legacy_exists:
                    cursor.execute("SELECT * FROM user_profile WHERE id = 1")
                    leg = cursor.fetchone()
                    if leg:
                        cursor.execute("""
                            INSERT INTO user_profiles (
                                user_id, full_name, monthly_income, salary_credit_day, emergency_buffer,
                                current_liquid_balance, monthly_essential_budget, monthly_savings_target
                            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            leg["full_name"], leg["monthly_income"], leg["salary_credit_day"],
                            leg["emergency_buffer"], leg["current_liquid_balance"],
                            leg["monthly_essential_budget"] if "monthly_essential_budget" in leg.keys() else 18000.0,
                            leg["monthly_savings_target"] if "monthly_savings_target" in leg.keys() else 10000.0
                        ))
                else:
                    cursor.execute("""
                        INSERT INTO user_profiles (
                            user_id, full_name, monthly_income, salary_credit_day, emergency_buffer,
                            current_liquid_balance, monthly_essential_budget, monthly_savings_target
                        ) VALUES (1, 'Aarav Sharma', 115000.0, 1, 15000.0, 62450.0, 18000.0, 10000.0)
                    """)

            # Ensure all orphaned obligations, transactions, and savings goals point to user 1
            cursor.execute("UPDATE obligations SET user_id = 1 WHERE user_id IS NULL OR user_id = 0")
            cursor.execute("UPDATE transactions SET user_id = 1 WHERE user_id IS NULL OR user_id = 0")
            cursor.execute("UPDATE savings_goals SET user_id = 1 WHERE user_id IS NULL OR user_id = 0")

            conn.commit()

        # Seed sample data for user 1 if completely empty
        self._seed_default_data_if_empty()

    def _seed_default_data_if_empty(self):
        """Seed initial sample financial records for default demo user (Aarav Sharma, user_id=1)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM obligations WHERE user_id = 1")
            obligations_count = cursor.fetchone()[0]

            if obligations_count == 0:
                default_obligations = [
                    (1, '2BHK Apartment Rent', 'Rent & Housing', 24000.0, 5, 1),
                    (1, 'HDFC Car Loan EMI', 'EMI & Debt Repayment', 12800.0, 10, 1),
                    (1, 'Parag Parikh Flexi Cap SIP', 'Investments & Mutual Funds (SIP)', 10000.0, 7, 1),
                    (1, 'Cook & Domestic Help Salary', 'Domestic Help & Maintenance', 6000.0, 5, 1),
                    (1, 'Airtel Fiber & Electricity Bill', 'Bills & Utilities (Electricity/WiFi)', 3200.0, 25, 0),
                    (1, 'Cult.fit Gym & Fitness Pass', 'Health, Medical & Gym', 2200.0, 28, 0),
                ]
                cursor.executemany("""
                    INSERT INTO obligations (user_id, title, category, amount, due_day, is_paid)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, default_obligations)

            cursor.execute("SELECT COUNT(*) FROM transactions WHERE user_id = 1")
            tx_count = cursor.fetchone()[0]

            if tx_count == 0:
                today = date.today()
                seed_txs = [
                    (1, (today - timedelta(days=20)).strftime("%Y-%m-%d"), 115000.0, 'income', 'Salary / Monthly Staging', 'Bank App (IMPS/NEFT)', 'TCS Payroll', 'November Salary Credit', 1),
                    (1, (today - timedelta(days=16)).strftime("%Y-%m-%d"), 24000.0, 'expense', 'Rent & Housing', 'Google Pay', 'Landlord (Ramesh K)', 'November Flat Rent via UPI', 1),
                    (1, (today - timedelta(days=14)).strftime("%Y-%m-%d"), 10000.0, 'expense', 'Investments & Mutual Funds (SIP)', 'Bank App (IMPS/NEFT)', 'Zerodha Coin', 'Monthly SIP Auto-debit', 1),
                    (1, (today - timedelta(days=11)).strftime("%Y-%m-%d"), 12800.0, 'expense', 'EMI & Debt Repayment', 'Bank App (IMPS/NEFT)', 'HDFC Bank AutoDebit', 'Car Loan EMI', 1),
                    (1, (today - timedelta(days=10)).strftime("%Y-%m-%d"), 6000.0, 'expense', 'Domestic Help & Maintenance', 'PhonePe', 'Sunita Devi', 'Cook & Maid monthly pay', 1),
                    (1, (today - timedelta(days=9)).strftime("%Y-%m-%d"), 649.0, 'expense', 'Entertainment & OTT', 'CRED UPI', 'Netflix India', 'Monthly Premium 4K plan', 0),
                    (1, (today - timedelta(days=8)).strftime("%Y-%m-%d"), 2150.0, 'expense', 'Commute & Fuel', 'PhonePe', 'Indian Oil Petrol Pump', 'Fuel for car', 1),
                    (1, (today - timedelta(days=7)).strftime("%Y-%m-%d"), 820.0, 'expense', 'Food & Dining (Swiggy/Zomato)', 'Google Pay', 'Zomato - Meghana Foods', 'Weekend Biryani dinner with friends', 0),
                    (1, (today - timedelta(days=6)).strftime("%Y-%m-%d"), 1450.0, 'expense', 'Quick Commerce & Groceries (Zepto/Blinkit)', 'PhonePe', 'Blinkit', 'Weekly vegetables and pantry snacks', 1),
                    (1, (today - timedelta(days=5)).strftime("%Y-%m-%d"), 350.0, 'expense', 'Food & Dining (Swiggy/Zomato)', 'Google Pay', 'Blue Tokai Coffee', 'Iced Americano & Croissant', 0),
                    (1, (today - timedelta(days=4)).strftime("%Y-%m-%d"), 285.0, 'expense', 'Commute & Fuel', 'Paytm', 'Uber India', 'Cab to office meeting', 1),
                    (1, (today - timedelta(days=3)).strftime("%Y-%m-%d"), 1890.0, 'expense', 'Shopping & E-Commerce', 'CRED UPI', 'Amazon India', 'Ergonomic Desk Mat & cables', 0),
                    (1, (today - timedelta(days=2)).strftime("%Y-%m-%d"), 620.0, 'expense', 'Food & Dining (Swiggy/Zomato)', 'Google Pay', 'Swiggy Instamart', 'Midnight snacks & energy drinks', 0),
                    (1, (today - timedelta(days=1)).strftime("%Y-%m-%d"), 480.0, 'expense', 'Health, Medical & Gym', 'Paytm', 'Apollo Pharmacy', 'Vitamins & Pain Relief spray', 1),
                    (1, today.strftime("%Y-%m-%d"), 240.0, 'expense', 'Food & Dining (Swiggy/Zomato)', 'PhonePe', 'Chai Point', 'Office tea & samosas', 0),
                ]
                cursor.executemany("""
                    INSERT INTO transactions (user_id, date, amount, type, category, upi_app, merchant, note, is_essential)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, seed_txs)

            cursor.execute("SELECT COUNT(*) FROM savings_goals WHERE user_id = 1")
            sg_count = cursor.fetchone()[0]

            if sg_count == 0:
                default_goals = [
                    (1, 'Emergency Fund (3-Month Reserve)', 75000.0, 35000.0, '2026-12-31'),
                    (1, 'MacBook Pro / Workstation', 80000.0, 24000.0, '2027-03-31'),
                    (1, 'Goa Vacation with Friends', 25000.0, 12500.0, '2026-12-25'),
                ]
                cursor.executemany("""
                    INSERT INTO savings_goals (user_id, title, target_amount, current_amount, target_date)
                    VALUES (?, ?, ?, ?, ?)
                """, default_goals)

            conn.commit()

    # =========================================================
    # USER AUTHENTICATION & MANAGEMENT
    # =========================================================

    def register_user(self, full_name: str, email: str, password_hash: str) -> Optional[int]:
        """
        Register a new user in the SQLite database.
        Returns new user ID if successful, or None if email already exists.
        """
        clean_email = email.strip().lower()
        clean_name = full_name.strip()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (clean_email,))
            if cursor.fetchone():
                return None  # Duplicate email

            cursor.execute("""
                INSERT INTO users (full_name, email, password_hash, account_status)
                VALUES (?, ?, ?, 'active')
            """, (clean_name, clean_email, password_hash))
            new_user_id = cursor.lastrowid

            # Initialize isolated starter financial profile for the new user
            cursor.execute("""
                INSERT INTO user_profiles (
                    user_id, full_name, monthly_income, salary_credit_day, emergency_buffer,
                    current_liquid_balance, monthly_essential_budget, monthly_savings_target
                ) VALUES (?, ?, 85000.0, 1, 15000.0, 45000.0, 18000.0, 10000.0)
            """, (new_user_id, clean_name))

            conn.commit()
            return new_user_id

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve user record by email (case-insensitive)."""
        clean_email = email.strip().lower()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (clean_email,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve user record by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_user_password(self, user_id: int, new_password_hash: str) -> bool:
        """Update password hash for a user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_user_name(self, user_id: int, new_name: str) -> bool:
        """Update full name in users and user_profiles tables."""
        clean_name = new_name.strip()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET full_name = ? WHERE id = ?", (clean_name, user_id))
            cursor.execute("UPDATE user_profiles SET full_name = ? WHERE user_id = ?", (clean_name, user_id))
            conn.commit()
            return True

    # =========================================================
    # PASSWORD RESET OPERATIONS
    # =========================================================

    def create_password_reset_otp(self, user_id: int, otp_code: str, expiry_minutes: int = 15) -> int:
        """Store a time-limited password reset OTP for a user."""
        expires_at = datetime.now() + timedelta(minutes=expiry_minutes)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Invalidate any previous unused OTPs for this user
            cursor.execute("UPDATE password_resets SET is_used = 1 WHERE user_id = ? AND is_used = 0", (user_id,))
            cursor.execute("""
                INSERT INTO password_resets (user_id, otp_code, expires_at, is_used)
                VALUES (?, ?, ?, 0)
            """, (user_id, otp_code, expires_at.strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            return cursor.lastrowid

    def verify_and_consume_otp(self, email: str, otp_code: str) -> Optional[int]:
        """
        Verify OTP for an email. Checks if OTP exists, is not used, and has not expired.
        If valid, marks as used and returns user_id; otherwise returns None.
        """
        user = self.get_user_by_email(email)
        if not user:
            return None

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM password_resets
                WHERE user_id = ? AND otp_code = ? AND is_used = 0 AND expires_at >= ?
                ORDER BY id DESC LIMIT 1
            """, (user["id"], otp_code.strip(), now_str))
            row = cursor.fetchone()
            if row:
                reset_id = row["id"]
                cursor.execute("UPDATE password_resets SET is_used = 1 WHERE id = ?", (reset_id,))
                conn.commit()
                return user["id"]
            return None

    # =========================================================
    # USER PROFILE OPERATIONS (USER-ISOLATED)
    # =========================================================

    def get_user_profile(self, user_id: int = 1) -> Dict[str, Any]:
        """Retrieve financial profile for a specific user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d.setdefault("monthly_essential_budget", 18000.0)
                d.setdefault("monthly_savings_target", 10000.0)
                return d

            # If user exists in users table, initialize profile automatically
            cursor.execute("SELECT full_name FROM users WHERE id = ?", (user_id,))
            u = cursor.fetchone()
            name = u["full_name"] if u else "User"
            cursor.execute("""
                INSERT INTO user_profiles (
                    user_id, full_name, monthly_income, salary_credit_day, emergency_buffer,
                    current_liquid_balance, monthly_essential_budget, monthly_savings_target
                ) VALUES (?, ?, 85000.0, 1, 15000.0, 45000.0, 18000.0, 10000.0)
            """, (user_id, name))
            conn.commit()

            return {
                "user_id": user_id,
                "full_name": name,
                "monthly_income": 85000.0,
                "salary_credit_day": 1,
                "emergency_buffer": 15000.0,
                "current_liquid_balance": 45000.0,
                "monthly_essential_budget": 18000.0,
                "monthly_savings_target": 10000.0
            }

    def update_user_profile(self, user_id: int, name: str, income: float, salary_day: int, emergency_buffer: float,
                            liquid_balance: float, essential_budget: float = 18000.0, savings_target: float = 10000.0):
        """Update financial profile for a specific user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_profiles
                SET full_name = ?, monthly_income = ?, salary_credit_day = ?, emergency_buffer = ?,
                    current_liquid_balance = ?, monthly_essential_budget = ?, monthly_savings_target = ?
                WHERE user_id = ?
            """, (name, income, salary_day, emergency_buffer, liquid_balance, essential_budget, savings_target, user_id))
            # Also keep full_name in sync in users table
            cursor.execute("UPDATE users SET full_name = ? WHERE id = ?", (name, user_id))
            conn.commit()

    # =========================================================
    # OBLIGATIONS OPERATIONS (USER-ISOLATED)
    # =========================================================

    def get_obligations(self, user_id: int = 1) -> pd.DataFrame:
        """Get recurring obligations for a specific user."""
        with self.get_connection() as conn:
            query = "SELECT * FROM obligations WHERE user_id = ? ORDER BY due_day ASC"
            return pd.read_sql_query(query, conn, params=(user_id,))

    def add_obligation(self, user_id: int, title: str, category: str, amount: float, due_day: int, is_paid: int = 0) -> int:
        """Add a recurring obligation for a specific user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO obligations (user_id, title, category, amount, due_day, is_paid)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, title, category, amount, due_day, is_paid))
            conn.commit()
            return cursor.lastrowid

    def update_obligation_paid_status(self, user_id: int, obligation_id: int, is_paid: int, deduct_from_balance: bool = False):
        """Update obligation paid status for a specific user with optional balance deduction."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM obligations WHERE id = ? AND user_id = ?", (obligation_id, user_id))
            ob = cursor.fetchone()
            if not ob:
                return

            cursor.execute("UPDATE obligations SET is_paid = ? WHERE id = ? AND user_id = ?", (is_paid, obligation_id, user_id))

            if deduct_from_balance and is_paid == 1:
                cursor.execute("""
                    INSERT INTO transactions (user_id, date, amount, type, category, upi_app, merchant, note, is_essential)
                    VALUES (?, ?, ?, 'expense', ?, 'Auto-Debit / UPI', ?, ?, 1)
                """, (user_id, str(date.today()), ob["amount"], ob["category"], ob["title"], f"Fixed Obligation Settled: {ob['title']}"))

                cursor.execute("""
                    UPDATE user_profiles
                    SET current_liquid_balance = current_liquid_balance - ?
                    WHERE user_id = ?
                """, (ob["amount"], user_id))

            conn.commit()

    def delete_obligation(self, user_id: int, obligation_id: int) -> bool:
        """Delete an obligation belonging to a specific user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM obligations WHERE id = ? AND user_id = ?", (obligation_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def reset_cycle_obligations(self, user_id: int = 1):
        """Reset recurring obligations' is_paid status to 0 for a specific user's fresh salary cycle."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE obligations SET is_paid = 0 WHERE user_id = ?", (user_id,))
            conn.commit()

    # =========================================================
    # TRANSACTIONS OPERATIONS (USER-ISOLATED)
    # =========================================================

    def get_transactions(self, user_id: int = 1, limit: Optional[int] = None) -> pd.DataFrame:
        """Get transactions for a specific user."""
        with self.get_connection() as conn:
            query = "SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC, id DESC"
            if limit:
                query += f" LIMIT {limit}"
            df = pd.read_sql_query(query, conn, params=(user_id,))
            return df

    def add_transaction(self, user_id: int, tx_date: str, amount: float, tx_type: str, category: str,
                        upi_app: str, merchant: str, note: str, is_essential: int = 0) -> int:
        """Add a transaction for a specific user and adjust user's liquid balance."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (user_id, date, amount, type, category, upi_app, merchant, note, is_essential)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, tx_date, amount, tx_type, category, upi_app, merchant, note, is_essential))
            tx_id = cursor.lastrowid

            balance_delta = amount if tx_type == 'income' else -amount
            cursor.execute("""
                UPDATE user_profiles
                SET current_liquid_balance = current_liquid_balance + ?
                WHERE user_id = ?
            """, (balance_delta, user_id))

            conn.commit()
            return tx_id

    def delete_transaction(self, user_id: int, tx_id: int) -> bool:
        """Delete a transaction belonging to a specific user and revert balance."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT amount, type FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
            row = cursor.fetchone()
            if row:
                amount, tx_type = row["amount"], row["type"]
                balance_delta = -amount if tx_type == 'income' else amount
                cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
                cursor.execute("""
                    UPDATE user_profiles
                    SET current_liquid_balance = current_liquid_balance + ?
                    WHERE user_id = ?
                """, (balance_delta, user_id))
                conn.commit()
                return True
            return False

    def add_transactions_batch(self, user_id: int, transactions_list: List[Dict[str, Any]]) -> int:
        """Batch insert transactions for a specific user (e.g. from CSV import or SMS parser)."""
        inserted_count = 0
        total_balance_delta = 0.0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for tx in transactions_list:
                amt = float(tx["amount"])
                tx_type = tx.get("type", "expense")
                cursor.execute("""
                    INSERT INTO transactions (user_id, date, amount, type, category, upi_app, merchant, note, is_essential)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    str(tx.get("date", date.today())),
                    amt,
                    tx_type,
                    tx.get("category", "Miscellaneous / Other"),
                    tx.get("upi_app", "Google Pay"),
                    tx.get("merchant", "Merchant"),
                    tx.get("note", "Imported via statement"),
                    int(tx.get("is_essential", 0))
                ))
                inserted_count += 1
                total_balance_delta += amt if tx_type == "income" else -amt

            cursor.execute("""
                UPDATE user_profiles
                SET current_liquid_balance = current_liquid_balance + ?
                WHERE user_id = ?
            """, (total_balance_delta, user_id))
            conn.commit()
        return inserted_count

    # =========================================================
    # SAVINGS GOALS OPERATIONS (USER-ISOLATED)
    # =========================================================

    def get_savings_goals(self, user_id: int = 1) -> pd.DataFrame:
        """Get savings goals for a specific user."""
        with self.get_connection() as conn:
            query = "SELECT * FROM savings_goals WHERE user_id = ? ORDER BY id ASC"
            return pd.read_sql_query(query, conn, params=(user_id,))

    def add_savings_goal(self, user_id: int, title: str, target_amount: float, current_amount: float = 0.0, target_date: str = None) -> int:
        """Add a savings goal for a specific user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO savings_goals (user_id, title, target_amount, current_amount, target_date)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, title, target_amount, current_amount, target_date))
            conn.commit()
            return cursor.lastrowid

    def update_savings_goal_progress(self, user_id: int, goal_id: int, added_amount: float, deduct_from_balance: bool = False):
        """Update savings goal progress for a specific user with optional balance deduction."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE savings_goals
                SET current_amount = current_amount + ?
                WHERE id = ? AND user_id = ?
            """, (added_amount, goal_id, user_id))
            if deduct_from_balance:
                cursor.execute("""
                    UPDATE user_profiles
                    SET current_liquid_balance = current_liquid_balance - ?
                    WHERE user_id = ?
                """, (added_amount, user_id))
            conn.commit()

    def delete_savings_goal(self, user_id: int, goal_id: int) -> bool:
        """Delete a savings goal belonging to a specific user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM savings_goals WHERE id = ? AND user_id = ?", (goal_id, user_id))
            conn.commit()
            return cursor.rowcount > 0


# Singleton database instance
db = DatabaseManager()
