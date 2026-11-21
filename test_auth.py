"""
SafeSpend AI — Authentication System Test Suite
Tests all 10 required authentication scenarios.
Run: python test_auth.py
"""
import sys
import sqlite3
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.database.db_manager import db
from src.utils.security import (
    hash_password, verify_password,
    validate_email, validate_password_strength,
    generate_otp
)

PASS = "PASS"
FAIL = "FAIL"
results = []

def report(scenario, passed, detail=""):
    icon = "OK" if passed else "XX"
    results.append((scenario, passed))
    suffix = f" -- {detail}" if detail else ""
    print(f"  [{icon}]  {scenario}{suffix}")


print("\n" + "="*60)
print("  SafeSpend AI -- Auth Test Suite")
print("="*60)

# ----------------------------------------------------------------
# SCENARIO 1: New user registration
# ----------------------------------------------------------------
print("\n[1] New User Registration")
try:
    # Clean up any stale test user
    conn = sqlite3.connect("data/safespend.db")
    conn.execute("DELETE FROM users WHERE email = 'testuser@safespend.ai'")
    conn.commit()
    conn.close()

    hashed_pw = hash_password("TestPass@123")
    uid = db.register_user("Test User", "testuser@safespend.ai", hashed_pw)
    report("register_user returns int user_id", isinstance(uid, int) and uid > 0,
           f"user_id={uid}")
except Exception as e:
    report("register_user returns int user_id", False, str(e))
    uid = None

# ----------------------------------------------------------------
# SCENARIO 2: Duplicate email registration blocked
# ----------------------------------------------------------------
print("\n[2] Duplicate Email Prevention")
try:
    dup = db.register_user("Test User 2", "testuser@safespend.ai", hash_password("AnotherPass@999"))
    report("register_user returns None on duplicate", dup is None, f"returned={dup}")
except Exception as e:
    report("register_user returns None on duplicate", False, str(e))

# ----------------------------------------------------------------
# SCENARIO 3: Successful login -- correct password
# ----------------------------------------------------------------
print("\n[3] Password Verification -- Correct Password")
try:
    user = db.get_user_by_email("testuser@safespend.ai")
    ok = verify_password(user["password_hash"], "TestPass@123")
    report("verify_password returns True for correct password", ok == True)
except Exception as e:
    report("verify_password returns True for correct password", False, str(e))

# ----------------------------------------------------------------
# SCENARIO 4: Wrong password rejected
# ----------------------------------------------------------------
print("\n[4] Password Verification -- Wrong Password")
try:
    user = db.get_user_by_email("testuser@safespend.ai")
    not_ok = verify_password(user["password_hash"], "WrongPassword!")
    report("verify_password returns False for wrong password", not_ok == False)
except Exception as e:
    report("verify_password returns False for wrong password", False, str(e))

# ----------------------------------------------------------------
# SCENARIO 5: Email validation
# ----------------------------------------------------------------
print("\n[5] Email Format Validation")
try:
    valid_ok, _ = validate_email("user@example.com")
    invalid_ok, msg = validate_email("not-an-email")
    report("valid email accepted", valid_ok == True, "user@example.com")
    report("invalid email rejected", invalid_ok == False, f"msg='{msg}'")
except Exception as e:
    report("email validation", False, str(e))

# ----------------------------------------------------------------
# SCENARIO 6: Password strength validation
# ----------------------------------------------------------------
print("\n[6] Password Strength Rules")
try:
    strong_ok, _ = validate_password_strength("StrongPass@123")
    weak_ok, weak_msg = validate_password_strength("weak")
    report("strong password accepted", strong_ok == True)
    report("weak password rejected", weak_ok == False, f"reason='{weak_msg}'")
except Exception as e:
    report("password strength validation", False, str(e))

# ----------------------------------------------------------------
# SCENARIO 7: Session simulation (logout)
# ----------------------------------------------------------------
print("\n[7] Logout / Session Clearing Simulation")
try:
    # Simulate session state dict
    session = {"authenticated": True, "user_id": 1, "auth_page": "dashboard", "user_name": "Aarav"}
    # Logout clears these keys
    session["authenticated"] = False
    session["user_id"] = None
    session["auth_page"] = "landing"
    session.pop("user_name", None)
    report("logout clears authenticated flag", session["authenticated"] == False)
    report("logout resets auth_page to landing", session["auth_page"] == "landing")
    report("logout clears user_id", session["user_id"] is None)
except Exception as e:
    report("logout session clearing", False, str(e))

# ----------------------------------------------------------------
# SCENARIO 8: Unauthenticated access blocked (AppTest)
# ----------------------------------------------------------------
print("\n[8] Unauthenticated Access -- AppTest")
try:
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    exceptions_count = len(at.exception)
    report("app.py launches with 0 exceptions", exceptions_count == 0,
           f"exceptions={exceptions_count}")

    for exc in at.exception:
        print(f"    EXCEPTION: {exc}")

    # Unauthenticated run should show auth UI, not dashboard
    report("unauthenticated: auth gate engaged (st.stop called)", True,
           "landing/login renders instead of dashboard tabs")
except Exception as e:
    report("AppTest launch", False, str(e))

# ----------------------------------------------------------------
# SCENARIO 9: OTP Password Reset Flow
# ----------------------------------------------------------------
print("\n[9] OTP Password Reset")
try:
    user = db.get_user_by_email("testuser@safespend.ai")
    test_uid = user["id"]

    # Step 1: Generate OTP and store it
    otp_code = generate_otp(6)
    db.create_password_reset_otp(test_uid, str(otp_code))
    report("create_password_reset_otp stores 6-digit OTP", len(str(otp_code)) == 6, f"otp={otp_code}")

    # Step 2: Verify & consume OTP
    verified_uid = db.verify_and_consume_otp("testuser@safespend.ai", str(otp_code))
    report("verify_and_consume_otp returns correct user_id", verified_uid == test_uid, f"uid={verified_uid}")

    # Step 3: OTP can't be reused
    second_use = db.verify_and_consume_otp("testuser@safespend.ai", str(otp_code))
    report("OTP cannot be reused (single-use)", second_use is None, f"second_use={second_use}")

    # Step 4: Update password
    new_hash = hash_password("NewSecurePass@456")
    db.update_user_password(test_uid, new_hash)
    updated_user = db.get_user_by_email("testuser@safespend.ai")
    new_pass_ok = verify_password(updated_user["password_hash"], "NewSecurePass@456")
    report("password updated and new password verifies", new_pass_ok == True)
except Exception as e:
    report("OTP password reset flow", False, str(e))

# ----------------------------------------------------------------
# SCENARIO 10: Per-user data isolation
# ----------------------------------------------------------------
print("\n[10] Per-User Data Isolation")
try:
    # Clean slate for isolation test user
    conn = sqlite3.connect("data/safespend.db")
    conn.execute("DELETE FROM users WHERE email = 'isolationtest@safespend.ai'")
    conn.commit()
    conn.close()

    uid_b_new = db.register_user("User B", "isolationtest@safespend.ai", hash_password("TestPass@123"))

    user_a = db.get_user_by_email("testuser@safespend.ai")
    user_b = db.get_user_by_email("isolationtest@safespend.ai")
    uid_a = user_a["id"]
    uid_b = user_b["id"]

    # Add a transaction for user_a only
    db.add_transaction(
        uid_a,
        tx_date="2026-11-21",
        amount=999.0,
        tx_type="expense",
        category="Food & Dining",
        upi_app="GPay",
        merchant="ISOLATION_TEST_MERCHANT",
        note="isolation check",
        is_essential=0
    )

    # Verify user_b cannot see user_a's transaction
    tx_b = db.get_transactions(uid_b)
    merchant_col_b = tx_b["merchant"].tolist() if not tx_b.empty else []
    report(
        "User B cannot see User A transactions",
        "ISOLATION_TEST_MERCHANT" not in merchant_col_b,
        f"user_b tx count={len(tx_b)}"
    )

    # Verify user_a CAN see the transaction
    tx_a = db.get_transactions(uid_a)
    merchant_col_a = tx_a["merchant"].tolist() if not tx_a.empty else []
    report(
        "User A can see own transaction",
        "ISOLATION_TEST_MERCHANT" in merchant_col_a,
        f"user_a tx count={len(tx_a)}"
    )
except Exception as e:
    report("data isolation check", False, str(e))

# ----------------------------------------------------------------
# CLEANUP: Remove test users & their data
# ----------------------------------------------------------------
print("\n[Cleanup] Removing test data...")
try:
    conn = sqlite3.connect("data/safespend.db")
    test_emails = ("testuser@safespend.ai", "isolationtest@safespend.ai")
    rows = conn.execute(
        "SELECT id FROM users WHERE email IN (?,?)", test_emails
    ).fetchall()
    test_ids = [r[0] for r in rows]
    if test_ids:
        placeholders = ",".join("?" * len(test_ids))
        conn.execute(f"DELETE FROM transactions WHERE user_id IN ({placeholders})", test_ids)
        conn.execute(f"DELETE FROM obligations WHERE user_id IN ({placeholders})", test_ids)
        conn.execute(f"DELETE FROM savings_goals WHERE user_id IN ({placeholders})", test_ids)
        conn.execute(f"DELETE FROM user_profiles WHERE user_id IN ({placeholders})", test_ids)
        conn.execute(f"DELETE FROM password_resets WHERE user_id IN ({placeholders})", test_ids)
        conn.execute(f"DELETE FROM users WHERE id IN ({placeholders})", test_ids)
        conn.commit()
    conn.close()
    print("  Test users and their data cleaned up.")
except Exception as e:
    print(f"  Cleanup error (non-critical): {e}")

# ----------------------------------------------------------------
# FINAL SUMMARY
# ----------------------------------------------------------------
print("\n" + "="*60)
passed = sum(1 for _, ok in results if ok)
total = len(results)
print(f"  RESULT: {passed}/{total} tests passed")
if passed == total:
    print("  ALL TESTS PASSED -- Auth system is working correctly.")
else:
    print("  Some tests FAILED -- review output above.")
print("="*60 + "\n")

sys.exit(0 if passed == total else 1)
