"""
Authentication UI for SafeSpend AI.
Landing page, Login, Sign Up, Forgot Password, and User Profile sidebar.
"""
import streamlit as st
from datetime import datetime
from src.database.db_manager import db
from src.utils.security import (
    hash_password, verify_password, validate_email,
    validate_password_strength, generate_otp
)


# ─────────────────────────────────────────────
# SHARED STYLES
# ─────────────────────────────────────────────
AUTH_CSS = """
<style>
.auth-logo {
    background: linear-gradient(135deg, #00F59B 0%, #8B5CF6 100%);
    width: 56px; height: 56px;
    border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.8rem;
    box-shadow: 0 4px 20px rgba(0,245,155,0.35);
    margin: 0 auto 1rem auto;
    text-align: center; line-height: 56px;
}
.auth-title {
    font-size: 1.5rem; font-weight: 800;
    color: #F8FAFC; text-align: center; margin-bottom: 0.25rem;
}
.auth-sub {
    font-size: 0.88rem; color: #64748B;
    text-align: center; margin-bottom: 1.5rem;
}
.landing-tagline {
    font-size: 2rem; font-weight: 800; color: #F8FAFC;
    line-height: 1.25; margin: 1rem 0 0.5rem 0; text-align: center;
}
.landing-desc {
    font-size: 0.95rem; color: #94A3B8;
    max-width: 420px; margin: 0 auto 2rem auto;
    line-height: 1.6; text-align: center;
}
.feature-pill {
    display: inline-block;
    background: rgba(0,245,155,0.1);
    border: 1px solid rgba(0,245,155,0.25);
    color: #00F59B; border-radius: 9999px;
    padding: 4px 14px; font-size: 0.78rem; font-weight: 600;
    margin: 3px;
}
.otp-box {
    background: #0A0E1A; border: 2px solid #00F59B;
    border-radius: 12px; padding: 1.25rem 1.5rem;
    text-align: center; margin: 1rem 0;
}
.otp-code {
    font-size: 2.2rem; font-weight: 800; color: #00F59B;
    letter-spacing: 10px; font-family: monospace;
}
.warning-banner {
    background: rgba(249,115,22,0.1);
    border: 1px solid rgba(249,115,22,0.3);
    border-radius: 10px; padding: 0.75rem 1rem;
    color: #F97316; font-size: 0.84rem; margin: 0.75rem 0;
}
</style>
"""


def _inject_css():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 1. LANDING PAGE
# ─────────────────────────────────────────────
def render_landing_page():
    _inject_css()

    st.markdown("<br>", unsafe_allow_html=True)

    # Hero section
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("""
        <div style="text-align:center;padding:1rem 0;">
            <div style="background:linear-gradient(135deg,#00F59B,#8B5CF6);width:80px;height:80px;
                        border-radius:22px;margin:0 auto 1rem auto;display:flex;align-items:center;
                        justify-content:center;font-size:2.5rem;box-shadow:0 6px 30px rgba(0,245,155,0.4);">
                ₹
            </div>
            <div style="font-size:1.1rem;font-weight:800;color:#F8FAFC;margin-bottom:0.5rem;">
                SafeSpend <span style="color:#00F59B;">AI</span>
            </div>
            <div class="landing-tagline">
                Your money.<br>Your decisions.<br>
                <span style="color:#00F59B;">Your future.</span>
            </div>
            <div class="landing-desc">
                India's most intelligent personal finance companion. Track UPI spends,
                ring-fence your bills, and get real-time safe-to-spend guidance powered by AI.
            </div>
            <div style="margin-bottom:2rem;">
                <span class="feature-pill">📊 Real-Time Dashboard</span>
                <span class="feature-pill">⚡ Safe-to-Spend Engine</span>
                <span class="feature-pill">🤖 AI Money Coach</span>
                <span class="feature-pill">📱 UPI Tracker</span>
                <span class="feature-pill">🛍️ Affordability Simulator</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀  Get Started →", use_container_width=True, type="primary", key="landing_get_started"):
            st.session_state["auth_page"] = "signup"
            st.rerun()

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Login", use_container_width=True, key="landing_login"):
                st.session_state["auth_page"] = "login"
                st.rerun()
        with c2:
            if st.button("Sign Up", use_container_width=True, key="landing_signup"):
                st.session_state["auth_page"] = "signup"
                st.rerun()

        st.markdown("""
        <div style="text-align:center;margin-top:2.5rem;padding-top:1.5rem;
                    border-top:1px solid #1E293B;">
            <div style="font-size:0.75rem;color:#334155;margin-bottom:0.4rem;">SECURITY STANDARDS</div>
            <div style="font-size:0.8rem;color:#475569;">
                🔒 Argon2id Password Hashing &nbsp;•&nbsp;
                💾 100% Local SQLite Storage &nbsp;•&nbsp;
                🛡️ Zero Plain-Text Credentials
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 2. LOGIN PAGE
# ─────────────────────────────────────────────
def render_login_page():
    _inject_css()

    col_l, col_c, col_r = st.columns([1, 1.5, 1])
    with col_c:
        if st.button("← Back", key="login_back"):
            st.session_state["auth_page"] = "landing"
            st.rerun()

        st.markdown("""
        <div style="background:#121A2D;border:1px solid #1E293B;border-radius:18px;
                    padding:2rem 1.75rem;margin:0.5rem 0;">
            <div class="auth-logo">₹</div>
            <div class="auth-title">Welcome back</div>
            <div class="auth-sub">Sign in to your SafeSpend AI account</div>
        </div>
        """, unsafe_allow_html=True)

        email = st.text_input("Email Address", placeholder="you@example.com", key="login_email")
        password = st.text_input("Password", type="password", placeholder="Your password",
                                 key="login_password")

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        if st.button("Login →", use_container_width=True, type="primary", key="login_submit"):
            _handle_login(email, password)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Forgot Password?", key="login_forgot"):
                st.session_state["auth_page"] = "forgot_password"
                st.rerun()
        with c2:
            if st.button("Create Account", key="login_to_signup"):
                st.session_state["auth_page"] = "signup"
                st.rerun()

        st.markdown("""
        <div style="background:#0A0E1A;border:1px solid #1E293B;border-radius:10px;
                    padding:0.85rem 1rem;margin-top:1.25rem;font-size:0.82rem;color:#64748B;">
            <strong style="color:#8B5CF6;">Demo Account</strong><br>
            📧 aarav@safespend.ai<br>
            🔑 SafeSpend@123
        </div>
        """, unsafe_allow_html=True)


def _handle_login(email: str, password: str):
    if not email.strip():
        st.error("Please enter your email address.")
        return
    if not password:
        st.error("Please enter your password.")
        return

    valid_email, email_err = validate_email(email)
    if not valid_email:
        st.error(f"Invalid email format: {email_err}")
        return

    user = db.get_user_by_email(email.strip())
    if not user:
        st.error("No account found with this email address.")
        return

    if user.get("account_status") == "suspended":
        st.error("This account has been suspended. Please contact support.")
        return

    if not verify_password(user["password_hash"], password):
        st.error("Incorrect password. Please try again.")
        return

    # Successful login — populate session state
    st.session_state["authenticated"] = True
    st.session_state["user_id"] = user["id"]
    st.session_state["user_email"] = user["email"]
    st.session_state["user_name"] = user["full_name"]
    st.session_state.pop("coach_messages", None)  # fresh chat per session
    st.rerun()


# ─────────────────────────────────────────────
# 3. SIGN UP PAGE
# ─────────────────────────────────────────────
def render_signup_page():
    _inject_css()

    col_l, col_c, col_r = st.columns([1, 1.5, 1])
    with col_c:
        if st.button("← Back", key="signup_back"):
            st.session_state["auth_page"] = "landing"
            st.rerun()

        st.markdown("""
        <div style="background:#121A2D;border:1px solid #1E293B;border-radius:18px;
                    padding:2rem 1.75rem;margin:0.5rem 0;">
            <div class="auth-logo">₹</div>
            <div class="auth-title">Create Account</div>
            <div class="auth-sub">Start your financial intelligence journey</div>
        </div>
        """, unsafe_allow_html=True)

        full_name = st.text_input("Full Name", placeholder="Priya Patel", key="signup_name")
        email = st.text_input("Email Address", placeholder="you@example.com", key="signup_email")
        password = st.text_input("Password", type="password",
                                 placeholder="Min 8 chars with upper, lower, number, symbol",
                                 key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password",
                                         placeholder="Re-enter your password",
                                         key="signup_confirm")

        st.markdown("""
        <div style="font-size:0.78rem;color:#475569;line-height:1.8;margin-bottom:0.75rem;
                    background:#0A0E1A;border-radius:8px;padding:0.6rem 0.9rem;">
            Password requirements:
            &nbsp;✓ 8+ characters &nbsp;
            ✓ Uppercase (A-Z) &nbsp;
            ✓ Lowercase (a-z) &nbsp;
            ✓ Number (0-9) &nbsp;
            ✓ Symbol (!@#$%...)
        </div>
        """, unsafe_allow_html=True)

        if st.button("Create Account →", use_container_width=True, type="primary", key="signup_submit"):
            _handle_signup(full_name, email, password, confirm_password)

        if st.button("Already have an account? Login", key="signup_to_login"):
            st.session_state["auth_page"] = "login"
            st.rerun()


def _handle_signup(full_name: str, email: str, password: str, confirm_password: str):
    errors = []

    if not full_name.strip() or len(full_name.strip()) < 2:
        errors.append("Full name must be at least 2 characters.")

    valid_email, email_err = validate_email(email)
    if not valid_email:
        errors.append(email_err)

    valid_pw, pw_err = validate_password_strength(password)
    if not valid_pw:
        errors.append(pw_err)

    if password and confirm_password and password != confirm_password:
        errors.append("Passwords do not match.")

    if errors:
        for e in errors:
            st.error(e)
        return

    pw_hash = hash_password(password)
    new_user_id = db.register_user(full_name.strip(), email.strip(), pw_hash)

    if new_user_id is None:
        st.error("An account with this email already exists. Please log in instead.")
        return

    st.success(f"Account created! Welcome, {full_name.strip().split()[0]}! Please sign in.")
    st.session_state["auth_page"] = "login"
    st.rerun()


# ─────────────────────────────────────────────
# 4. FORGOT PASSWORD PAGE
# ─────────────────────────────────────────────
def render_forgot_password_page():
    _inject_css()

    col_l, col_c, col_r = st.columns([1, 1.5, 1])
    with col_c:
        if st.button("← Back to Login", key="forgot_back"):
            # Clean up any pending OTP state
            for k in ["fp_otp_shown", "fp_otp_value", "fp_email_used"]:
                st.session_state.pop(k, None)
            st.session_state["auth_page"] = "login"
            st.rerun()

        st.markdown("""
        <div style="background:#121A2D;border:1px solid #1E293B;border-radius:18px;
                    padding:2rem 1.75rem;margin:0.5rem 0;">
            <div class="auth-logo" style="font-size:1.6rem;">🔑</div>
            <div class="auth-title">Reset Password</div>
            <div class="auth-sub">Enter your email to receive a reset code</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="warning-banner">
            ⚠️ <strong>No email service is configured.</strong> The OTP will appear directly on
            this page. In production, configure SMTP (see setup guide) to send it to your inbox.
        </div>
        """, unsafe_allow_html=True)

        # ── STEP 1: Request OTP ──
        st.markdown("#### Step 1: Enter Registered Email")
        fp_email = st.text_input("Email Address", placeholder="you@example.com", key="fp_email")

        if st.button("Generate Reset Code", use_container_width=True, key="fp_request"):
            _handle_otp_request(fp_email)

        # Show OTP if generated
        if st.session_state.get("fp_otp_shown"):
            otp_val = st.session_state["fp_otp_value"]
            st.markdown(f"""
            <div class="otp-box">
                <div style="font-size:0.82rem;color:#94A3B8;margin-bottom:0.5rem;">
                    Your 6-digit Reset Code (valid 15 minutes):
                </div>
                <div class="otp-code">{otp_val}</div>
                <div style="font-size:0.75rem;color:#475569;margin-top:0.5rem;">
                    Copy this code — use it in Step 2 below
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── STEP 2: Verify OTP & Set New Password ──
            st.markdown("---")
            st.markdown("#### Step 2: Set New Password")
            otp_input = st.text_input("Reset Code", placeholder="6-digit code", key="fp_otp_input",
                                      max_chars=6)
            new_pw = st.text_input("New Password", type="password",
                                   placeholder="New strong password", key="fp_new_pw")
            confirm_pw = st.text_input("Confirm New Password", type="password",
                                       placeholder="Re-enter new password", key="fp_confirm_pw")

            if st.button("Reset Password →", use_container_width=True, type="primary", key="fp_reset"):
                _handle_password_reset(
                    st.session_state.get("fp_email_used", ""),
                    otp_input, new_pw, confirm_pw
                )


def _handle_otp_request(email: str):
    valid_email, email_err = validate_email(email)
    if not valid_email:
        st.error(f"Invalid email: {email_err}")
        return

    user = db.get_user_by_email(email.strip())
    if not user:
        # Don't reveal whether the email is registered
        st.warning("If this email is registered, a reset code has been generated below.")
        return

    otp = generate_otp(6)
    db.create_password_reset_otp(user["id"], otp, expiry_minutes=15)
    st.session_state["fp_otp_shown"] = True
    st.session_state["fp_otp_value"] = otp
    st.session_state["fp_email_used"] = email.strip().lower()
    st.rerun()


def _handle_password_reset(email: str, otp_code: str, new_pw: str, confirm_pw: str):
    if not otp_code.strip():
        st.error("Please enter the 6-digit reset code.")
        return

    valid_pw, pw_err = validate_password_strength(new_pw)
    if not valid_pw:
        st.error(pw_err)
        return

    if new_pw != confirm_pw:
        st.error("Passwords do not match.")
        return

    user_id = db.verify_and_consume_otp(email, otp_code.strip())
    if user_id is None:
        st.error("Invalid or expired reset code. Please request a new one.")
        for k in ["fp_otp_shown", "fp_otp_value", "fp_email_used"]:
            st.session_state.pop(k, None)
        st.rerun()
        return

    db.update_user_password(user_id, hash_password(new_pw))

    for k in ["fp_otp_shown", "fp_otp_value", "fp_email_used"]:
        st.session_state.pop(k, None)

    st.success("✅ Password reset successfully! Please log in with your new password.")
    st.session_state["auth_page"] = "login"
    st.rerun()


# ─────────────────────────────────────────────
# 5. USER PROFILE SIDEBAR SECTION
# ─────────────────────────────────────────────
def render_user_profile_sidebar(user: dict):
    """Render authenticated user card and logout in the sidebar."""
    if not user:
        return

    name = user.get("full_name", "User")
    email = user.get("email", "")
    created_raw = user.get("created_at", "")
    initials = "".join(w[0].upper() for w in name.split()[:2]) or "U"

    created_display = ""
    if created_raw:
        try:
            dt = datetime.fromisoformat(str(created_raw).replace("Z", ""))
            created_display = dt.strftime("%b %Y")
        except Exception:
            created_display = str(created_raw)[:7]

    st.markdown(f"""
    <div style="padding:8px 0 12px 0;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <div style="background:linear-gradient(135deg,#00F59B,#8B5CF6);border-radius:50%;
                        width:40px;height:40px;display:flex;align-items:center;justify-content:center;
                        font-size:0.9rem;font-weight:800;color:#0A0E1A;flex-shrink:0;">
                {initials}
            </div>
            <div style="overflow:hidden;">
                <div style="font-weight:700;color:#F8FAFC;font-size:0.88rem;
                            overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{name}</div>
                <div style="font-size:0.72rem;color:#64748B;
                            overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{email}</div>
                <div style="font-size:0.68rem;color:#334155;">Member since {created_display}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("✏️ Edit Profile", expanded=False):
        new_display_name = st.text_input("Display Name", value=name, key="sidebar_edit_name")
        if st.button("Save Name", key="sidebar_save_name", use_container_width=True):
            if new_display_name.strip() and len(new_display_name.strip()) >= 2:
                uid = st.session_state.get("user_id", 1)
                db.update_user_name(uid, new_display_name.strip())
                st.session_state["user_name"] = new_display_name.strip()
                st.success("Name updated!")
                st.rerun()
            else:
                st.error("Name must be at least 2 characters.")

    if st.button("🚪  Logout", key="sidebar_logout", use_container_width=True):
        for key in ["authenticated", "user_id", "user_email", "user_name",
                    "coach_messages", "survival_override",
                    "fp_otp_shown", "fp_otp_value", "fp_email_used"]:
            st.session_state.pop(key, None)
        st.session_state["auth_page"] = "landing"
        st.rerun()
