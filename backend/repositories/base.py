"""
Base Repository.

Generic repository pattern for database operations.
Provides common CRUD operations for all models.
"""

from typing import TypeVar, Generic, Type

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    Base repository with common CRUD operations.

    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: AsyncSession):
                super().__init__(session, User)
    """

    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> T | None:
        """Get a single record by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """Get all records with pagination."""
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, obj: T) -> T:
        """Create a new record."""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def save(self, obj: T) -> T:
        """Save changes to an existing record."""
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: T) -> None:
        """Delete a record."""
        await self.session.delete(obj)
        await self.session.commit()

    async def flush(self) -> None:
        """Flush pending changes without commit."""
        await self.session.flush()

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()
