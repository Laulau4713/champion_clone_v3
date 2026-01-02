"""
Pytest Configuration and Fixtures.

Provides:
- In-memory SQLite database for tests
- Async client for API testing
- Test user and auth fixtures
"""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database import get_db
from main import app
from models import Base, User
from services.auth import create_access_token, hash_password

# ============================================
# Database Fixtures
# ============================================

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create a fresh database engine for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    async_session_maker = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        yield session


# ============================================
# API Client Fixtures
# ============================================


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for API testing."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ============================================
# User Fixtures
# ============================================


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database."""
    user = User(
        email="test@example.com", hashed_password=hash_password("TestPass123$"), full_name="Test User", is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def inactive_user(db_session: AsyncSession) -> User:
    """Create an inactive test user."""
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password("TestPass123$"),
        full_name="Inactive User",
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user in the database."""
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("AdminPass123$"),
        full_name="Admin User",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
def auth_headers(test_user: User) -> dict:
    """Create authorization headers with valid JWT token."""
    token = create_access_token(test_user.id, test_user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
def admin_auth_headers(admin_user: User) -> dict:
    """Create authorization headers with admin JWT token."""
    token = create_access_token(admin_user.id, admin_user.email)
    return {"Authorization": f"Bearer {token}"}


# ============================================
# Test Data
# ============================================


@pytest.fixture
def valid_user_data() -> dict:
    """Valid user registration data."""
    return {"email": "newuser@example.com", "password": "ValidPass123$", "full_name": "New User"}


@pytest.fixture
def weak_password_data() -> dict:
    """User data with weak password (passes Pydantic min_length but fails our policy)."""
    return {
        "email": "weak@example.com",
        "password": "weakpassword",  # 12 chars but no uppercase, digit, or special
        "full_name": "Weak Password User",
    }
