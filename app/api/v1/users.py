from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.repositories.kelas import KelasRepository
from app.repositories.session import SessionRepository
from app.repositories.user import UserRepository
from app.schemas.common import Envelope, PaginatedEnvelope
from app.schemas.user import (
    BulkUserDeactivateSummary,
    BulkUserIdsRequest,
    CreateUserRequest,
    ResetPasswordRequest,
    UpdateUserRequest,
    UserFilterParams,
    UserResponse,
)
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])

DbSession = Annotated[Session, Depends(get_db)]


def get_user_service() -> UserService:
    return UserService(UserRepository(), KelasRepository(), SessionRepository())


@router.post(
    "",
    response_model=Envelope[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: CreateUserRequest,
    db: DbSession,
    requester: Annotated[User, Depends(require_permission("user:create"))],
    service: Annotated[UserService, Depends(get_user_service)],
):
    return Envelope(data=service.create(db, requester, payload))


@router.get("", response_model=PaginatedEnvelope[UserResponse])
def list_users(
    db: DbSession,
    requester: Annotated[User, Depends(require_permission("user:read"))],
    service: Annotated[UserService, Depends(get_user_service)],
    role: Annotated[str | None, Query()] = None,
    carian: Annotated[str | None, Query()] = None,
    page: Annotated[int | None, Query()] = None,
    page_size: Annotated[int | None, Query()] = None,
):
    filters = UserFilterParams(role=role, carian=carian, page=page, page_size=page_size)
    data, meta = service.list(db, requester, filters)
    return PaginatedEnvelope(data=data, meta=meta)


@router.get("/{user_id}", response_model=Envelope[UserResponse])
def get_user(
    user_id: int,
    db: DbSession,
    requester: Annotated[User, Depends(require_permission("user:read"))],
    service: Annotated[UserService, Depends(get_user_service)],
):
    return Envelope(data=service.get_by_id(db, requester, user_id))


@router.patch("/{user_id}", response_model=Envelope[UserResponse])
def update_user(
    user_id: int,
    payload: UpdateUserRequest,
    db: DbSession,
    requester: Annotated[User, Depends(require_permission("user:update"))],
    service: Annotated[UserService, Depends(get_user_service)],
):
    return Envelope(data=service.update(db, requester, user_id, payload))


@router.post("/{user_id}/reset-password", response_model=Envelope[UserResponse])
def reset_password(
    user_id: int,
    payload: ResetPasswordRequest,
    db: DbSession,
    requester: Annotated[User, Depends(require_permission("user:reset_password"))],
    service: Annotated[UserService, Depends(get_user_service)],
):
    return Envelope(
        data=service.reset_password(db, requester, user_id, payload.kata_laluan_baru)
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_user(
    user_id: int,
    db: DbSession,
    requester: Annotated[User, Depends(require_permission("user:delete"))],
    service: Annotated[UserService, Depends(get_user_service)],
):
    service.soft_delete(db, requester, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/bulk-deactivate",
    response_model=Envelope[BulkUserDeactivateSummary],
)
def bulk_deactivate_users(
    payload: BulkUserIdsRequest,
    db: DbSession,
    requester: Annotated[User, Depends(require_permission("user:delete"))],
    service: Annotated[UserService, Depends(get_user_service)],
):
    return Envelope(data=service.soft_delete_many(db, requester, payload.ids))