from __future__ import annotations

from sqlalchemy.orm import Session

from app.api.deps import KELAS_SCOPE_ALL, KelasScope, resolve_kelas_scope
from app.core.exceptions import (
    InvalidTargetRoleError,
    NoPermissionError,
    ResourceNotFoundError,
    UsernameTakenError,
    ValidationError,
)
from app.core.pagination import normalize_pagination
from app.core.security import hash_password
from app.models.user import User
from app.repositories.kelas import KelasRepository
from app.repositories.session import SessionRepository
from app.repositories.user import UserRepository
from app.schemas.user import (
    CreateUserRequest,
    UpdateUserRequest,
    UserFilterParams,
    UserResponse,
)

ROLE_TARGET_WHITELIST: dict[str, set[str]] = {
    "super_admin": {"admin", "murid"},
    "admin": {"murid"},
}


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        kelas_repository: KelasRepository,
        session_repository: SessionRepository,
    ) -> None:
        self._user_repository = user_repository
        self._kelas_repository = kelas_repository
        self._session_repository = session_repository

    def create(
        self, db: Session, requester: User, payload: CreateUserRequest
    ) -> UserResponse:
        target_role = payload.role
        if target_role not in ROLE_TARGET_WHITELIST.get(requester.role, set()):
            raise InvalidTargetRoleError()

        username = payload.username.strip().lower()
        if self._user_repository.get_by_username(db, username) is not None:
            raise UsernameTakenError()

        kelas_id = payload.kelas_id
        if target_role == "murid":
            if kelas_id is None:
                raise ValidationError("Kelas wajib diisi untuk murid.")
            self._semak_kelas_dalam_skop_own(db, requester, kelas_id)
        elif kelas_id is not None:
            raise ValidationError("Kelas hanya untuk akaun murid.")

        user = self._user_repository.create(
            db,
            username=username,
            nama_first=payload.nama_first.strip(),
            nama_last=payload.nama_last.strip(),
            password_hash=hash_password(payload.kata_laluan_awal),
            role=target_role,
            aktif=True,
            mesti_tukar_kata_laluan=True,
            kelas_id=kelas_id,
            created_by=requester.id,
        )
        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)

    def list(
        self,
        db: Session,
        requester: User,
        filters: UserFilterParams,
    ) -> tuple[list[UserResponse], dict]:
        scope = resolve_kelas_scope(db, requester)
        kelas_ids = None if scope is KELAS_SCOPE_ALL else set(scope.visible)

        page, page_size = normalize_pagination(filters.page, filters.page_size)
        offset = (page - 1) * page_size
        users, total_items = self._user_repository.list(
            db,
            role=filters.role,
            carian=filters.carian,
            kelas_ids=kelas_ids,
            offset=offset,
            limit=page_size,
        )
        responses = [UserResponse.model_validate(user) for user in users]
        meta = {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": (
                (total_items + page_size - 1) // page_size if total_items > 0 else 0
            ),
        }
        return responses, meta

    def get_by_id(
        self, db: Session, requester: User, user_id: int
    ) -> UserResponse:
        user = self._get_user_atau_404(db, user_id)
        self._semak_boleh_baca(db, requester, user)
        return UserResponse.model_validate(user)

    def update(
        self,
        db: Session,
        requester: User,
        user_id: int,
        payload: UpdateUserRequest,
    ) -> UserResponse:
        user = self._get_user_atau_404(db, user_id)
        self._semak_skop_tulis(db, requester, user)

        changes: dict = {}
        if payload.nama_first is not None:
            changes["nama_first"] = payload.nama_first.strip()
        if payload.nama_last is not None:
            changes["nama_last"] = payload.nama_last.strip()
        if payload.aktif is not None:
            changes["aktif"] = payload.aktif
        if payload.kelas_id is not None:
            self._semak_kelas_dalam_skop_own(db, requester, payload.kelas_id)
            changes["kelas_id"] = payload.kelas_id

        if not changes:
            return UserResponse.model_validate(user)

        updated = self._user_repository.update(db, user, **changes)
        if changes.get("aktif") is False:
            self._session_repository.revoke_all_for_user(db, user.id)
        db.commit()
        db.refresh(updated)
        return UserResponse.model_validate(updated)

    def reset_password(
        self, db: Session, requester: User, user_id: int, kata_laluan_baru: str
    ) -> UserResponse:
        user = self._get_user_atau_404(db, user_id)
        self._semak_skop_tulis(db, requester, user)
        user.password_hash = hash_password(kata_laluan_baru)
        user.mesti_tukar_kata_laluan = True
        self._session_repository.revoke_all_for_user(db, user.id)
        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)

    def soft_delete(self, db: Session, requester: User, user_id: int) -> None:
        user = self._get_user_atau_404(db, user_id)
        self._semak_skop_tulis(db, requester, user)
        user.aktif = False
        self._session_repository.revoke_all_for_user(db, user.id)
        db.commit()

    def _get_user_atau_404(self, db: Session, user_id: int) -> User:
        user = self._user_repository.get_by_id(db, user_id)
        if user is None:
            raise ResourceNotFoundError("Pengguna tidak dijumpai.")
        return user

    def _semak_kelas_dalam_skop_own(
        self, db: Session, requester: User, kelas_id: int
    ) -> None:
        kelas = self._kelas_repository.get_by_id(db, kelas_id)
        if kelas is None:
            raise ResourceNotFoundError("Kelas tidak dijumpai.")
        if requester.role != "super_admin":
            own = self._kelas_repository.get_guru_kelas_ids(db, requester.id)
            if kelas_id not in own:
                raise NoPermissionError()

    def _semak_boleh_baca(self, db: Session, requester: User, target: User) -> None:
        if requester.role == "super_admin":
            return
        if target.role != "murid":
            raise NoPermissionError()
        scope: KelasScope = resolve_kelas_scope(db, requester)
        if target.kelas_id is None or target.kelas_id not in scope.visible:
            raise NoPermissionError()

    def _semak_skop_tulis(self, db: Session, requester: User, target: User) -> None:
        if requester.role == "super_admin":
            return
        if target.role != "murid":
            raise NoPermissionError()
        own = self._kelas_repository.get_guru_kelas_ids(db, requester.id)
        if target.kelas_id is None or target.kelas_id not in own:
            raise NoPermissionError()