from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.kelas import Kelas
from app.models.kelas_assignment import GuruKelas, KelasShare
from app.models.user import User


class KelasRepository:
    def list_kelas(
        self, db: Session, *, kelas_ids: set[int] | None = None
    ) -> list[Kelas]:
        stmt = select(Kelas).order_by(Kelas.id)
        if kelas_ids is not None:
            stmt = stmt.where(Kelas.id.in_(kelas_ids))
        return list(db.scalars(stmt))

    def get_by_id(self, db: Session, kelas_id: int) -> Kelas | None:
        return db.get(Kelas, kelas_id)

    def create(self, db: Session, *, nama: str, darjah: int) -> Kelas:
        kelas = Kelas(nama=nama, darjah=darjah)
        db.add(kelas)
        db.flush()
        return kelas

    def update(self, db: Session, kelas: Kelas, **changes) -> Kelas:
        for field, value in changes.items():
            setattr(kelas, field, value)
        db.flush()
        return kelas

    def get_guru_kelas_ids(self, db: Session, user_id: int) -> set[int]:
        stmt = select(GuruKelas.kelas_id).where(GuruKelas.guru_id == user_id)
        return set(db.scalars(stmt))

    def get_shared_kelas_ids(self, db: Session, user_id: int) -> set[int]:
        stmt = select(KelasShare.kelas_id).where(
            KelasShare.shared_with_guru_id == user_id
        )
        return set(db.scalars(stmt))

    def get_owner_ids(self, db: Session, kelas_id: int) -> set[int]:
        stmt = select(GuruKelas.guru_id).where(GuruKelas.kelas_id == kelas_id)
        return set(db.scalars(stmt))

    def list_owners_for_kelas(
        self, db: Session, kelas_ids: list[int]
    ) -> dict[int, list[User]]:
        if not kelas_ids:
            return {}
        stmt = (
            select(GuruKelas.kelas_id, User)
            .join(User, GuruKelas.guru_id == User.id)
            .where(GuruKelas.kelas_id.in_(kelas_ids))
        )
        result: dict[int, list[User]] = {}
        for kelas_id, user in db.execute(stmt):
            result.setdefault(kelas_id, []).append(user)
        return result

    def list_shares_for_kelas(
        self, db: Session, kelas_ids: list[int]
    ) -> dict[int, list[User]]:
        if not kelas_ids:
            return {}
        stmt = (
            select(KelasShare.kelas_id, User)
            .join(User, KelasShare.shared_with_guru_id == User.id)
            .where(KelasShare.kelas_id.in_(kelas_ids))
        )
        result: dict[int, list[User]] = {}
        for kelas_id, user in db.execute(stmt):
            result.setdefault(kelas_id, []).append(user)
        return result

    def add_guru_kelas(
        self, db: Session, *, guru_id: int, kelas_id: int
    ) -> None:
        wujud = db.scalar(
            select(GuruKelas).where(
                GuruKelas.guru_id == guru_id, GuruKelas.kelas_id == kelas_id
            )
        )
        if wujud is None:
            db.add(GuruKelas(guru_id=guru_id, kelas_id=kelas_id))
            db.flush()

    def share_kelas(self, db: Session, kelas_id: int, guru_ids: list[int]) -> None:
        db.execute(
            delete(KelasShare).where(KelasShare.kelas_id == kelas_id)
        )
        for guru_id in guru_ids:
            db.add(KelasShare(kelas_id=kelas_id, shared_with_guru_id=guru_id))
        db.flush()

    def get_users_by_ids(self, db: Session, user_ids: list[int]) -> list[User]:
        if not user_ids:
            return []
        stmt = select(User).where(User.id.in_(user_ids))
        return list(db.scalars(stmt))

    def list_gurus_for_directory(self, db: Session) -> list[User]:
        stmt = (
            select(User)
            .where(User.role == "admin", User.aktif.is_(True))
            .order_by(User.nama_first, User.id)
        )
        return list(db.scalars(stmt))