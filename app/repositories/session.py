from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.session import UserSession


class SessionRepository:
    def create(
        self,
        db: Session,
        *,
        token_hash: str,
        user_id: int,
        expires_at: datetime,
        last_seen_at: datetime,
    ) -> UserSession:
        session = UserSession(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            last_seen_at=last_seen_at,
        )
        db.add(session)
        db.flush()
        return session

    def get_by_token_hash(self, db: Session, token_hash: str) -> UserSession | None:
        return db.scalar(select(UserSession).where(UserSession.token_hash == token_hash))

    def revoke(self, db: Session, session: UserSession) -> None:
        session.revoked_at = datetime.now(timezone.utc)
        db.flush()

    def touch(
        self,
        db: Session,
        session: UserSession,
        *,
        last_seen_at: datetime,
        expires_at: datetime,
    ) -> None:
        session.last_seen_at = last_seen_at
        session.expires_at = expires_at
        db.flush()

    def revoke_all_for_user(
        self, db: Session, user_id: int, *, exclude_token_hash: str | None = None
    ) -> int:
        stmt = (
            update(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )
        if exclude_token_hash is not None:
            stmt = stmt.where(UserSession.token_hash != exclude_token_hash)
        result = db.execute(stmt)
        return result.rowcount or 0

    def revoke_all_other_sessions(
        self, db: Session, user_id: int, current_token_hash: str
    ) -> int:
        return self.revoke_all_for_user(
            db, user_id, exclude_token_hash=current_token_hash
        )