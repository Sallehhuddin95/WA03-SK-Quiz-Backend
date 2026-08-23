import os
from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv

load_dotenv()

_configured_url = os.environ.get("DATABASE_URL")
if _configured_url:
    _parts = urlparse(_configured_url)
    _test_url = urlunparse(
        (_parts.scheme, _parts.netloc, "/sk_quiz_test", "", "", "")
    )
else:
    _test_url = "postgresql+psycopg://postgres:postgres@localhost:5432/sk_quiz_test"

os.environ["DATABASE_URL"] = _test_url

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from alembic import command
from alembic.config import Config
from app.core.database import engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _migrate_database():
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def _clean_tables(_migrate_database):
    yield
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE quiz_answers, quiz_attempts, questions "
                "RESTART IDENTITY CASCADE"
            )
        )


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)