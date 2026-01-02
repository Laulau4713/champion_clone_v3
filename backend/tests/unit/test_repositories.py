"""
Unit Tests for Repositories.

Tests repository layer functions:
- UserRepository CRUD operations
- ChampionRepository CRUD operations
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models import Champion, User
from repositories import ChampionRepository, UserRepository
from services.auth import hash_password


class TestUserRepository:
    """Tests for UserRepository."""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        """Should create a new user in database."""
        repo = UserRepository(db_session)

        user = User(email="new@example.com", hashed_password=hash_password("TestPass123$"), full_name="New User")
        created = await repo.create(user)

        assert created.id is not None
        assert created.email == "new@example.com"
        assert created.full_name == "New User"

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession, test_user: User):
        """Should retrieve user by ID."""
        repo = UserRepository(db_session)

        found = await repo.get_by_id(test_user.id)

        assert found is not None
        assert found.id == test_user.id
        assert found.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """Should return None for non-existent user."""
        repo = UserRepository(db_session)

        found = await repo.get_by_id(99999)

        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_email(self, db_session: AsyncSession, test_user: User):
        """Should retrieve user by email."""
        repo = UserRepository(db_session)

        found = await repo.get_by_email(test_user.email)

        assert found is not None
        assert found.id == test_user.id

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, db_session: AsyncSession):
        """Should return None for non-existent email."""
        repo = UserRepository(db_session)

        found = await repo.get_by_email("nonexistent@example.com")

        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_id_active(self, db_session: AsyncSession, test_user: User):
        """Should retrieve active user by ID."""
        repo = UserRepository(db_session)

        found = await repo.get_by_id_active(test_user.id)

        assert found is not None
        assert found.is_active is True

    @pytest.mark.asyncio
    async def test_get_by_id_active_returns_none_for_inactive(self, db_session: AsyncSession, inactive_user: User):
        """Should return None for inactive user."""
        repo = UserRepository(db_session)

        found = await repo.get_by_id_active(inactive_user.id)

        assert found is None

    @pytest.mark.asyncio
    async def test_email_exists_true(self, db_session: AsyncSession, test_user: User):
        """Should return True when email exists."""
        repo = UserRepository(db_session)

        exists = await repo.email_exists(test_user.email)

        assert exists is True

    @pytest.mark.asyncio
    async def test_email_exists_false(self, db_session: AsyncSession):
        """Should return False when email doesn't exist."""
        repo = UserRepository(db_session)

        exists = await repo.email_exists("nonexistent@example.com")

        assert exists is False


class TestChampionRepository:
    """Tests for ChampionRepository."""

    @pytest.mark.asyncio
    async def test_create_champion(self, db_session: AsyncSession):
        """Should create a new champion."""
        repo = ChampionRepository(db_session)

        champion = Champion(name="Test Champion", description="A test champion", status="uploaded")
        created = await repo.create(champion)

        assert created.id is not None
        assert created.name == "Test Champion"
        assert created.status == "uploaded"

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession):
        """Should retrieve champion by ID."""
        repo = ChampionRepository(db_session)

        champion = Champion(name="Test", status="uploaded")
        created = await repo.create(champion)

        found = await repo.get_by_id(created.id)

        assert found is not None
        assert found.name == "Test"

    @pytest.mark.asyncio
    async def test_get_all_ordered(self, db_session: AsyncSession):
        """Should retrieve all champions ordered by creation date."""
        repo = ChampionRepository(db_session)

        # Create multiple champions
        for i in range(3):
            await repo.create(Champion(name=f"Champion {i}", status="uploaded"))

        all_champions = await repo.get_all_ordered()

        assert len(all_champions) == 3

    @pytest.mark.asyncio
    async def test_get_all_ordered_with_status_filter(self, db_session: AsyncSession):
        """Should filter champions by status."""
        repo = ChampionRepository(db_session)

        await repo.create(Champion(name="Ready", status="ready"))
        await repo.create(Champion(name="Uploaded", status="uploaded"))

        ready_champions = await repo.get_all_ordered(status="ready")

        assert len(ready_champions) == 1
        assert ready_champions[0].name == "Ready"

    @pytest.mark.asyncio
    async def test_delete_champion(self, db_session: AsyncSession):
        """Should delete a champion."""
        repo = ChampionRepository(db_session)

        champion = Champion(name="ToDelete", status="uploaded")
        created = await repo.create(champion)
        champion_id = created.id

        await repo.delete(created)

        found = await repo.get_by_id(champion_id)
        assert found is None
