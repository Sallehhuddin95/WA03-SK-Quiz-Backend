"""Kebergantungan FastAPI: pengesahan sesi dan kebenaran RBAC.

Skop kelas mengikut ADR 0007: super_admin tidak terikat, admin melihat
kelas milik sendiri (own) dan kelas kongsi (shared), murid terikat kepada
percubaan sendiri.
"""

from dataclasses import dataclass
from typing import Annotated, Literal

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import (
    MustChangePasswordError,
    NoPermissionError,
    SessionExpiredError,
)
from app.core.security import SESSION_COOKIE_NAME
from app.models.user import User
from app.repositories.kelas import KelasRepository
from app.repositories.session import SessionRepository
from app.repositories.user import UserRepository
from app.schemas.user import Role
from app.services.auth import AuthService

Permission = Literal[
    "user:create",
    "user:read",
    "user:update",
    "user:reset_password",
    "user:delete",
    "kelas:create",
    "kelas:read",
    "kelas:update",
    "kelas:share",
    "guru:directory",
    "attempt:create",
    "attempt:submit",
    "attempt:read_own",
    "attempt:read_all",
    "attempt:preview",
    "question:manage",
    "reference:read",
]

ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    "super_admin": frozenset(
        {
            "user:create",
            "user:read",
            "user:update",
            "user:reset_password",
            "user:delete",
            "kelas:create",
            "kelas:read",
            "kelas:update",
            "kelas:share",
            "guru:directory",
            "attempt:read_all",
            "attempt:preview",
            "question:manage",
            "reference:read",
        }
    ),
    "admin": frozenset(
        {
            "user:create",
            "user:read",
            "user:update",
            "user:reset_password",
            "user:delete",
            "kelas:read",
            "kelas:share",
            "guru:directory",
            "attempt:read_all",
            "attempt:preview",
            "question:manage",
            "reference:read",
        }
    ),
    "murid": frozenset(
        {
            "attempt:create",
            "attempt:submit",
            "attempt:read_own",
            "reference:read",
        }
    ),
}

DbSession = Annotated[Session, Depends(get_db)]


def _get_auth_service() -> AuthService:
    return AuthService(SessionRepository(), UserRepository())


def _get_kelas_repository() -> KelasRepository:
    return KelasRepository()


@dataclass(frozen=True)
class KelasScope:
    own: frozenset[int]
    shared: frozenset[int]

    @property
    def visible(self) -> frozenset[int]:
        return self.own | self.shared


class _AllKelasScope:
    """Sentinel untuk super_admin: skop tidak terikat."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "KELAS_SCOPE_ALL"


KELAS_SCOPE_ALL = _AllKelasScope()

_LALUAN_BEBAS_TUKAR_KATA_LALUAN = (
    "/auth/change-password",
    "/auth/logout",
    "/auth/me",
)


def _laluan_dikecualikan(path: str) -> bool:
    return any(path.endswith(suffix) for suffix in _LALUAN_BEBAS_TUKAR_KATA_LALUAN)


def get_current_user(
    request: Request, db: DbSession
) -> User:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise SessionExpiredError()
    user = _get_auth_service().get_session_user(db, token)
    if user.mesti_tukar_kata_laluan and not _laluan_dikecualikan(request.url.path):
        raise MustChangePasswordError()
    return user


def require_permission(permission: Permission):
    def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if permission not in ROLE_PERMISSIONS[current_user.role]:
            raise NoPermissionError()
        return current_user

    return dependency


def require_any_permission(*permissions: Permission):
    def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        allowed = ROLE_PERMISSIONS[current_user.role]
        if not any(permission in allowed for permission in permissions):
            raise NoPermissionError()
        return current_user

    return dependency


def resolve_kelas_scope(db: Session, user: User) -> KelasScope | _AllKelasScope:
    if user.role == "super_admin":
        return KELAS_SCOPE_ALL
    repository = _get_kelas_repository()
    own = repository.get_guru_kelas_ids(db, user.id)
    shared = repository.get_shared_kelas_ids(db, user.id)
    return KelasScope(own=frozenset(own), shared=frozenset(shared))