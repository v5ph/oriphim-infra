"""Pytest configuration and fixtures for Oriphim tests."""

import os
from pathlib import Path

import pytest


_TEST_DB_PATH = Path(__file__).resolve().parents[1] / ".watcher_test.db"


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> None:
    """Configure shared file-backed DB for tests and clean up at session end."""
    os.environ["SQLITE_DB_PATH"] = str(_TEST_DB_PATH)
    os.environ["DATABASE_ENCRYPTION_KEY"] = "0" * 64
    if "JWT_SECRET_KEY" not in os.environ:
        os.environ["JWT_SECRET_KEY"] = "test-secret-key-" + ("x" * 48)

    if _TEST_DB_PATH.exists():
        _TEST_DB_PATH.unlink()

    yield

    if _TEST_DB_PATH.exists():
        _TEST_DB_PATH.unlink()


@pytest.fixture(autouse=True)
def reset_database() -> None:
    """Reset DB before each test and initialize required schemas."""
    from app.core.storage import init_db
    from app.core.onboarding import init_onboarding_db

    db_path = Path(os.environ["SQLITE_DB_PATH"])
    if db_path.exists():
        db_path.unlink()

    init_db()
    init_onboarding_db()

    yield


@pytest.fixture
def test_client():
    """FastAPI TestClient with configured test database."""
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)
