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
from sqlalchemy.orm import Session

from alembic import command
from alembic.config import Config
from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.main import app
from app.repositories.kelas import KelasRepository
from app.repositories.user import UserRepository

TRUNCATE_TABLES = (
    "quiz_answers",
    "quiz_attempts",
    "questions",
    "sessions",
    "guru_kelas",
    "kelas_share",
    "users",
    "kelas",
)


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
                "TRUNCATE "
                + ", ".join(TRUNCATE_TABLES)
                + " RESTART IDENTITY CASCADE"
            )
        )


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def user_factory(db: Session):
    repository = UserRepository()

    def _create(
        *,
        username: str,
        password: str = "rahasia123",
        role: str = "murid",
        nama_first: str = "Ahmad",
        nama_last: str = "bin Ali",
        aktif: bool = True,
        mesti_tukar_kata_laluan: bool = False,
        kelas_id: int | None = None,
    ):
        user = repository.create(
            db,
            username=username,
            nama_first=nama_first,
            nama_last=nama_last,
            password_hash=hash_password(password),
            role=role,
            aktif=aktif,
            mesti_tukar_kata_laluan=mesti_tukar_kata_laluan,
            kelas_id=kelas_id,
            created_by=None,
        )
        db.commit()
        db.refresh(user)
        return user

    return _create


@pytest.fixture()
def kelas_factory(db: Session):
    repository = KelasRepository()

    def _create(*, nama: str, darjah: int = 6):
        kelas = repository.create(db, nama=nama, darjah=darjah)
        db.commit()
        db.refresh(kelas)
        return kelas

    return _create


@pytest.fixture()
def assign_owner(db: Session):
    repository = KelasRepository()

    def _assign(*, guru_id: int, kelas_id: int):
        repository.add_guru_kelas(db, guru_id=guru_id, kelas_id=kelas_id)
        db.commit()

    return _assign