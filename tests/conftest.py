import sys
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

os.environ.setdefault("JWT_SECRET", "test_secret")
os.environ["SUPABASE_DATABASE_URL"] = "sqlite+aiosqlite:///./test_fieldlog.db"

from database import Base, get_db
from main import app

TEST_DB_URL = "sqlite+aiosqlite:///./test_fieldlog.db"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    try:
        if os.path.exists("test_fieldlog.db"):
            os.remove("test_fieldlog.db")
    except PermissionError:
        pass  # Windows may still hold the sqlite file lock; harmless


@pytest_asyncio.fixture
async def client():
    from auth import create_token
    token = create_token()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as c:
        yield c
