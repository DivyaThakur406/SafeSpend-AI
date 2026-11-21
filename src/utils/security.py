"""
Security and Authentication Utilities for SafeSpend AI.
Handles Argon2 password hashing, verification, password complexity validation,
and email format validation.
"""
import re
import secrets
from typing import Tuple, Optional
import argon2
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

# Argon2 Password Hasher instance with recommended parameters
_hasher = argon2.PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MiB
    parallelism=4,
    hash_len=32,
    salt_len=16
)

# Email validation regex (RFC 5322 compliant simplified)
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)


def hash_password(password: str) -> str:
    """Hash a plain-text password using Argon2id."""
    if not password:
        raise ValueError("Password cannot be empty")
    return _hasher.hash(password)


def verify_password(stored_hash: str, provided_password: str) -> bool:
    """
    Verify a provided plain-text password against a stored Argon2 hash.
    Returns True if valid, False otherwise.
    """
    if not stored_hash or not provided_password:
        return False
    try:
        return _hasher.verify(stored_hash, provided_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email address format.
    Returns (is_valid, error_message).
    """
    if not email or not email.strip():
        return False, "Email address is required."
    clean_email = email.strip()
    if len(clean_email) > 254:
        return False, "Email address is too long."
    if not EMAIL_REGEX.match(clean_email):
        return False, "Please enter a valid email address (e.g., user@example.com)."
    return True, ""


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Enforce strong password requirements:
    - Minimum 8 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one number (0-9)
    - At least one special character (!@#$%^&* etc.)
    """
    if not password:
        return False, "Password is required."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password is too long (maximum 128 characters)."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter (a-z)."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\/]', password):
        return False, "Password must contain at least one special character (e.g. !@#$%^&*)."
    return True, ""


def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP."""
    # e.g., 6 digits: 100000 to 999999
    lower = 10 ** (length - 1)
    upper = (10 ** length) - 1
    return str(secrets.randbelow(upper - lower + 1) + lower)
