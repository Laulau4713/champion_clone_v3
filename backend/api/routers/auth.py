"""
Authentication Router.

Endpoints:
- POST /auth/register - Register new user
- POST /auth/login - Login and get tokens
- GET /auth/me - Get current user info
- POST /auth/refresh - Refresh access token
- POST /auth/logout - Logout (revoke refresh token)
- POST /auth/logout-all - Logout from all devices
"""

from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, Request
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from domain.exceptions import (
    AlreadyExistsError,
    AuthenticationError,
    ValidationError,
)
from models import RefreshToken, User
from repositories import RefreshTokenRepository, UserRepository
from schemas import PasswordChange, RefreshTokenRequest, Token, UserLogin, UserRegister, UserResponse, UserUpdate
from services.auth import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    validate_password,
    verify_password,
    verify_refresh_token,
)

settings = get_settings()
logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["Auth"])


# ============================================
# Dependencies
# ============================================


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    """
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid authorization header")

    token = auth_header[7:]

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
        if user_id is None:
            raise AuthenticationError("Invalid token")
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id_active(user_id)

    if user is None:
        raise AuthenticationError("User not found or inactive")

    return user


async def require_enterprise_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to require Enterprise plan access.

    Used for Champion V1 features (video analysis, pattern extraction).
    Non-enterprise users should use the Skills/Learning system instead.

    Raises HTTPException 403 if user doesn't have Enterprise plan.
    """
    from fastapi import HTTPException

    from models import SubscriptionPlan

    if current_user.subscription_plan != SubscriptionPlan.ENTERPRISE.value:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "ENTERPRISE_REQUIRED",
                "message": "La fonctionnalité Champion est réservée aux comptes Enterprise.",
                "suggestion": "Utilisez les sessions d'entraînement Skills pour vous former, "
                "ou contactez-nous pour découvrir l'offre Enterprise.",
                "current_plan": current_user.subscription_plan,
                "upgrade_url": "/enterprise",
            },
        )

    return current_user


# ============================================
# Endpoints
# ============================================


@router.post("/register", response_model=UserResponse)
async def register(request: Request, body: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    Register a new user account.

    Password requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter (A-Z)
    - At least 1 lowercase letter (a-z)
    - At least 1 digit (0-9)
    - At least 1 special character (!@#$%^&*...)
    """
    user_repo = UserRepository(db)

    # Validate password strength
    is_valid, error_message = validate_password(body.password)
    if not is_valid:
        raise ValidationError(error_message)

    # Check if email already exists
    if await user_repo.email_exists(body.email):
        raise AlreadyExistsError("User", "email", body.email)

    # Create new user
    user = User(email=body.email, hashed_password=hash_password(body.password), full_name=body.full_name)
    user = await user_repo.create(user)

    logger.info("user_registered", user_id=user.id, email=user.email)

    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(request: Request, body: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Login and get JWT access and refresh tokens.

    Use the access token in the Authorization header: `Bearer <token>`
    """
    user_repo = UserRepository(db)
    token_repo = RefreshTokenRepository(db)

    # Find user by email
    user = await user_repo.get_by_email(body.email)

    # DEBUG
    logger.info("login_attempt", email=body.email, user_found=user is not None)
    if user:
        pwd_valid = verify_password(body.password, user.hashed_password)
        logger.info("password_check", valid=pwd_valid, hash_prefix=user.hashed_password[:20])

    # Verify user exists and password is correct
    if not user or not verify_password(body.password, user.hashed_password):
        raise AuthenticationError("Invalid email or password")

    if not user.is_active:
        raise AuthenticationError("Account is inactive")

    # Create tokens
    access_token = create_access_token(user.id, user.email)
    refresh_token, token_hash, expires_at = create_refresh_token(user.id, user.email)

    # Store refresh token in database
    db_refresh_token = RefreshToken(
        token_hash=token_hash,
        user_id=user.id,
        expires_at=expires_at,
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host if request.client else None,
    )
    await token_repo.create(db_refresh_token)

    logger.info("user_logged_in", user_id=user.id, email=user.email)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user's information."""
    return UserResponse.model_validate(current_user)


@router.post("/refresh", response_model=Token)
async def refresh_access_token(request: Request, body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """
    Refresh an expired access token using a valid refresh token.
    """
    user_repo = UserRepository(db)
    token_repo = RefreshTokenRepository(db)

    try:
        payload = verify_refresh_token(body.refresh_token)
    except JWTError as e:
        logger.warning("refresh_token_invalid", error=str(e))
        raise AuthenticationError("Invalid or expired refresh token")

    token_hash = hash_refresh_token(body.refresh_token)

    # Check if token exists and is not revoked
    db_token = await token_repo.get_valid_token(token_hash)

    if not db_token:
        logger.warning("refresh_token_not_found_or_revoked", token_hash=token_hash[:16])
        raise AuthenticationError("Refresh token has been revoked")

    if db_token.expires_at < datetime.utcnow():
        logger.warning("refresh_token_expired", user_id=db_token.user_id)
        raise AuthenticationError("Refresh token has expired")

    # Get the user
    user = await user_repo.get_by_id_active(db_token.user_id)

    if not user:
        raise AuthenticationError("User not found or inactive")

    new_access_token = create_access_token(user.id, user.email)

    logger.info("token_refreshed", user_id=user.id)

    return Token(
        access_token=new_access_token,
        refresh_token=body.refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    request: Request,
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Logout by revoking the refresh token."""
    token_repo = RefreshTokenRepository(db)

    token_hash = hash_refresh_token(body.refresh_token)
    db_token = await token_repo.get_user_token(token_hash, current_user.id)

    if db_token:
        db_token.is_revoked = True
        await token_repo.save(db_token)
        logger.info("user_logged_out", user_id=current_user.id)

    return {"message": "Successfully logged out"}


@router.post("/logout-all")
async def logout_all_devices(
    request: Request, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Logout from all devices by revoking all refresh tokens."""
    token_repo = RefreshTokenRepository(db)

    await token_repo.revoke_all_user_tokens(current_user.id)

    logger.info("user_logged_out_all_devices", user_id=current_user.id)

    return {"message": "Successfully logged out from all devices"}


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    body: UserUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Update current user's profile (name, email)."""
    user_repo = UserRepository(db)

    # Check if new email is already taken
    if body.email and body.email != current_user.email:
        if await user_repo.email_exists(body.email):
            raise AlreadyExistsError("User", "email", body.email)
        current_user.email = body.email

    if body.full_name is not None:
        current_user.full_name = body.full_name

    await user_repo.save(current_user)

    logger.info("user_profile_updated", user_id=current_user.id)

    return UserResponse.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    body: PasswordChange, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Change current user's password."""
    user_repo = UserRepository(db)

    # Verify current password
    if not verify_password(body.current_password, current_user.hashed_password):
        raise AuthenticationError("Current password is incorrect")

    # Validate new password strength
    is_valid, error_message = validate_password(body.new_password)
    if not is_valid:
        raise ValidationError(error_message)

    # Update password
    current_user.hashed_password = hash_password(body.new_password)
    await user_repo.save(current_user)

    logger.info("user_password_changed", user_id=current_user.id)

    return {"message": "Password changed successfully"}
