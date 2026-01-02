"""
User Repository.

Database operations for User model.
"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import RefreshToken, User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id_active(self, user_id: int) -> User | None:
        """Get active user by ID."""
        result = await self.session.execute(select(User).where(User.id == user_id, User.is_active == True))
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Check if email is already registered."""
        user = await self.get_by_email(email)
        return user is not None


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository for RefreshToken model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, RefreshToken)

    async def get_valid_token(self, token_hash: str) -> RefreshToken | None:
        """Get non-revoked token by hash."""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash, RefreshToken.is_revoked == False)
        )
        return result.scalar_one_or_none()

    async def get_user_token(self, token_hash: str, user_id: int) -> RefreshToken | None:
        """Get token by hash and user ID."""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash, RefreshToken.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def revoke_all_user_tokens(self, user_id: int) -> None:
        """Revoke all refresh tokens for a user."""
        await self.session.execute(update(RefreshToken).where(RefreshToken.user_id == user_id).values(is_revoked=True))
        await self.session.commit()
