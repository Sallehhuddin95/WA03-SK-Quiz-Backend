from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    AccountDisabledError,
    InvalidCredentialsError,
    SessionExpiredError,
)
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.models.session import UserSession
from app.models.user import User
from app.repositories.session import SessionRepository
from app.repositories.user import UserRepository
from app.schemas.auth import SessionUserResponse
from app.schemas.kelas import KelasBrief

_settings = get_settings()


class AuthService:
    def __init__(
        self,
        session_repository: SessionRepository,
        user_repository: UserRepository,
    ) -> None:
        self._session_repository = session_repository
        self._user_repository = user_repository

    def login(self, db: Session, username: str, password: str) -> tuple[User, str]:
        user = self._user_repository.get_by_username(db, username.strip().lower())
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        if not user.aktif:
            raise AccountDisabledError()
        token = self.create_session(db, user)
        db.commit()
        return user, token

    def create_session(self, db: Session, user: User) -> str:
        token = generate_session_token()
        now = datetime.now(timezone.utc)
        self._session_repository.create(
            db,
            token_hash=hash_session_token(token),
            user_id=user.id,
            expires_at=now + timedelta(days=_settings.session_max_days),
            last_seen_at=now,
        )
        return token

    def logout(self, db: Session, token: str) -> None:
        session = self._session_repository.get_by_token_hash(
            db, hash_session_token(token)
        )
        if session is None:
            raise SessionExpiredError()
        self._session_repository.revoke(db, session)
        db.commit()

    def get_session_user(self, db: Session, token: str) -> User:
        session = self._session_repository.get_by_token_hash(
            db, hash_session_token(token)
        )
        if session is None:
            raise SessionExpiredError()
        if session.revoked_at is not None:
            raise SessionExpiredError()

        now = datetime.now(timezone.utc)
        if session.expires_at is None or session.expires_at < now:
            raise SessionExpiredError()
        if now - session.last_seen_at > timedelta(
            minutes=_settings.session_idle_minutes
        ):
            raise SessionExpiredError()

        self._renew_session(db, session, now)
        user = session.user
        if user is None:
            raise SessionExpiredError()
        if not user.aktif:
            raise AccountDisabledError()
        return user

    def change_password(
        self, db: Session, user: User, token: str, semasa: str, baru: str
    ) -> None:
        if not verify_password(semasa, user.password_hash):
            raise InvalidCredentialsError()
        user.password_hash = hash_password(baru)
        user.mesti_tukar_kata_laluan = False
        self._session_repository.revoke_all_other_sessions(
            db, user.id, hash_session_token(token)
        )
        db.commit()

    def to_session_user(self, db: Session, user: User) -> SessionUserResponse:
        kelas = None
        if user.kelas_id is not None:
            k = user.kelas
            if k is not None:
                kelas = KelasBrief(id=k.id, nama=k.nama, darjah=k.darjah)
        return SessionUserResponse(
            id=user.id,
            username=user.username,
            nama_first=user.nama_first,
            nama_last=user.nama_last,
            role=user.role,
            mesti_tukar_kata_laluan=user.mesti_tukar_kata_laluan,
            kelas=kelas,
        )

    def _renew_session(
        self, db: Session, session: UserSession, now: datetime
    ) -> None:
        had_absolut = session.created_at + timedelta(days=_settings.session_max_days)
        baru_expires = min(now + timedelta(days=_settings.session_max_days), had_absolut)
        self._session_repository.touch(
            db, session, last_seen_at=now, expires_at=baru_expires
        )