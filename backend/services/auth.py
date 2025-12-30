"""
Authentication Service.

Provides authentication utilities:
- Password hashing and verification
- JWT token creation and verification
- Password validation
"""

import re
import hashlib
import secrets
from datetime import datetime, timedelta

import bcrypt
from jose import jwt, JWTError
import structlog

from config import get_settings

settings = get_settings()
logger = structlog.get_logger()


# ============================================
# Password Functions
# ============================================

def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password against security policy.

    Requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter (A-Z)
    - At least 1 lowercase letter (a-z)
    - At least 1 digit (0-9)
    - At least 1 special character (!@#$%^&*...)

    Returns:
        (True, "") if valid
        (False, "error message") if invalid
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter (A-Z)"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter (a-z)"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit (0-9)"

    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;\':",./<>?]', password):
        return False, "Password must contain at least one special character (!@#$%^&*...)"

    return True, ""


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode('utf-8')[:72]  # bcrypt limit
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# ============================================
# JWT Token Functions
# ============================================

def create_access_token(user_id: int, email: str) -> str:
    """Create a JWT access token."""
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: int, email: str) -> tuple[str, str, datetime]:
    """
    Create a refresh token.
    Returns: (token, token_hash, expires_at)
    """
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token_id = secrets.token_urlsafe(32)

    refresh_secret = settings.REFRESH_TOKEN_SECRET or (settings.JWT_SECRET + "_refresh")

    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "refresh",
        "jti": token_id,
        "exp": expires_at,
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, refresh_secret, algorithm=settings.JWT_ALGORITHM)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    return token, token_hash, expires_at


def verify_refresh_token(token: str) -> dict:
    """
    Verify a refresh token and return its payload.
    Raises JWTError if invalid.
    """
    refresh_secret = settings.REFRESH_TOKEN_SECRET or (settings.JWT_SECRET + "_refresh")
    payload = jwt.decode(token, refresh_secret, algorithms=[settings.JWT_ALGORITHM])

    if payload.get("type") != "refresh":
        raise JWTError("Invalid token type")

    return payload


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token for database lookup."""
    return hashlib.sha256(token.encode()).hexdigest()


def decode_access_token(token: str) -> dict:
    """
    Decode and verify an access token.
    Raises JWTError if invalid.
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
