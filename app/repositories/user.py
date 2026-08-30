from __future__ import annotations

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def create(
        self,
        db: Session,
        *,
        username: str,
        nama_first: str,
        nama_last: str,
        password_hash: str,
        role: str,
        aktif: bool = True,
        mesti_tukar_kata_laluan: bool = True,
        kelas_id: int | None = None,
        created_by: int | None = None,
    ) -> User:
        user = User(
            username=username,
            nama_first=nama_first,
            nama_last=nama_last,
            password_hash=password_hash,
            role=role,
            aktif=aktif,
            mesti_tukar_kata_laluan=mesti_tukar_kata_laluan,
            kelas_id=kelas_id,
            created_by=created_by,
        )
        db.add(user)
        db.flush()
        return user

    def get_by_username(self, db: Session, username: str) -> User | None:
        return db.scalar(select(User).where(User.username == username))

    def get_by_id(self, db: Session, user_id: int) -> User | None:
        return db.get(User, user_id)

    def get_by_ids(self, db: Session, user_ids: list[int]) -> list[User]:
        stmt = select(User).where(User.id.in_(user_ids))
        return list(db.scalars(stmt))

    def bulk_update_aktif(self, db: Session, user_ids: list[int], aktif: bool) -> int:
        stmt = update(User).where(User.id.in_(user_ids)).values(aktif=aktif)
        result = db.execute(stmt)
        return result.rowcount or 0

    def list(
        self,
        db: Session,
        *,
        role: str | None,
        carian: str | None,
        kelas_ids: set[int] | None,
        offset: int,
        limit: int,
    ) -> tuple[list[User], int]:
        filters = []
        if role is not None:
            filters.append(User.role == role)
        if carian:
            pola = f"%{carian}%"
            filters.append(
                or_(
                    User.nama_first.ilike(pola),
                    User.nama_last.ilike(pola),
                    User.username.ilike(pola),
                )
            )
        if kelas_ids is not None:
            filters.append(User.kelas_id.in_(kelas_ids))

        count_stmt = select(func.count()).select_from(User).where(*filters)
        total_items = db.scalar(count_stmt) or 0

        stmt = (
            select(User)
            .where(*filters)
            .order_by(User.id)
            .offset(offset)
            .limit(limit)
        )
        return list(db.scalars(stmt)), total_items

    def update(self, db: Session, user: User, **changes) -> User:
        for field, value in changes.items():
            setattr(user, field, value)
        db.flush()
        return user

    def count(self, db: Session) -> int:
        return db.scalar(select(func.count()).select_from(User)) or 0
