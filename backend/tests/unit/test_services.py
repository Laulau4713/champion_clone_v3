"""
Unit Tests for Services.

Tests auth service functions:
- Password hashing and verification
- Password validation
- JWT token creation and verification
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError

from services.auth import (
    hash_password,
    verify_password,
    validate_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    hash_refresh_token,
    decode_access_token,
)
from config import get_settings

settings = get_settings()


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_different_hash(self):
        """Hash should be different from original password."""
        password = "TestPass123$"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are ~60 chars

    def test_hash_password_different_each_time(self):
        """Same password should produce different hashes (due to salt)."""
        password = "TestPass123$"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Correct password should verify successfully."""
        password = "TestPass123$"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Incorrect password should fail verification."""
        password = "TestPass123$"
        hashed = hash_password(password)

        assert verify_password("WrongPass123$", hashed) is False

    def test_verify_password_empty(self):
        """Empty password should fail verification."""
        hashed = hash_password("TestPass123$")

        assert verify_password("", hashed) is False


class TestPasswordValidation:
    """Tests for password policy validation."""

    def test_validate_password_valid(self):
        """Valid password should pass all checks."""
        is_valid, error = validate_password("ValidPass123$")

        assert is_valid is True
        assert error == ""

    def test_validate_password_too_short(self):
        """Password shorter than 8 chars should fail."""
        is_valid, error = validate_password("Ab1$")

        assert is_valid is False
        assert "8 characters" in error

    def test_validate_password_no_uppercase(self):
        """Password without uppercase should fail."""
        is_valid, error = validate_password("validpass123$")

        assert is_valid is False
        assert "uppercase" in error

    def test_validate_password_no_lowercase(self):
        """Password without lowercase should fail."""
        is_valid, error = validate_password("VALIDPASS123$")

        assert is_valid is False
        assert "lowercase" in error

    def test_validate_password_no_digit(self):
        """Password without digit should fail."""
        is_valid, error = validate_password("ValidPass$$")

        assert is_valid is False
        assert "digit" in error

    def test_validate_password_no_special(self):
        """Password without special char should fail."""
        is_valid, error = validate_password("ValidPass123")

        assert is_valid is False
        assert "special" in error


class TestJWTTokens:
    """Tests for JWT token functions."""

    def test_create_access_token_valid(self):
        """Access token should be creatable and decodable."""
        user_id = 1
        email = "test@example.com"

        token = create_access_token(user_id, email)
        payload = decode_access_token(token)

        assert payload["sub"] == str(user_id)
        assert payload["email"] == email
        assert payload["type"] == "access"

    def test_create_refresh_token_returns_tuple(self):
        """Refresh token creation should return token, hash, and expiry."""
        user_id = 1
        email = "test@example.com"

        token, token_hash, expires_at = create_refresh_token(user_id, email)

        assert token is not None
        assert len(token_hash) == 64  # SHA256 hex
        assert expires_at > datetime.utcnow()

    def test_verify_refresh_token_valid(self):
        """Valid refresh token should verify successfully."""
        user_id = 1
        email = "test@example.com"

        token, _, _ = create_refresh_token(user_id, email)
        payload = verify_refresh_token(token)

        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"

    def test_hash_refresh_token_consistent(self):
        """Same token should produce same hash."""
        token = "test_token_string"

        hash1 = hash_refresh_token(token)
        hash2 = hash_refresh_token(token)

        assert hash1 == hash2
        assert len(hash1) == 64

    def test_decode_invalid_token_raises(self):
        """Decoding invalid token should raise JWTError."""
        with pytest.raises(JWTError):
            decode_access_token("invalid.token.here")
