from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.repositories.kelas import KelasRepository
from app.schemas.common import Envelope
from app.schemas.kelas import (
    CreateKelasRequest,
    KelasResponse,
    ShareKelasRequest,
    UpdateKelasRequest,
)
from app.schemas.user import GuruDirectoryResponse
from app.services.kelas import KelasService

router = APIRouter(prefix="/kelas", tags=["kelas"])
guru_router = APIRouter(tags=["gurus"])

DbSession = Annotated[Session, Depends(get_db)]


def get_kelas_service() -> KelasService:
    return KelasService(KelasRepository())


@router.get("", response_model=Envelope[list[KelasResponse]])
def list_kelas(
    db: DbSession,
    requester: Annotated[User, Depends(require_permission("kelas:read"))],
    service: Annotated[KelasService, Depends(get_kelas_service)],
):
    return Envelope(data=service.list(db, requester))


@router.post(
    "",
    response_model=Envelope[KelasResponse],
    status_code=201,
)
def create_kelas(
    payload: CreateKelasRequest,
    db: DbSession,
    requester: Annotated[User, Depends(require_permission("kelas:create"))],
    service: Annotated[KelasService, Depends(get_kelas_service)],
):
    return Envelope(data=service.create(db, requester, payload))


@router.patch("/{kelas_id}", response_model=Envelope[KelasResponse])
def update_kelas(
    kelas_id: int,
    payload: UpdateKelasRequest,
    db: DbSession,
    requester: Annotated[User, Depends(require_permission("kelas:update"))],
    service: Annotated[KelasService, Depends(get_kelas_service)],
):
    return Envelope(data=service.update(db, requester, kelas_id, payload))


@router.put("/{kelas_id}/share", response_model=Envelope[KelasResponse])
def share_kelas(
    kelas_id: int,
    payload: ShareKelasRequest,
    db: DbSession,
    requester: Annotated[User, Depends(require_permission("kelas:share"))],
    service: Annotated[KelasService, Depends(get_kelas_service)],
):
    return Envelope(data=service.share(db, requester, kelas_id, payload.guru_ids))


@guru_router.get("/gurus", response_model=Envelope[list[GuruDirectoryResponse]])
def list_gurus(
    db: DbSession,
    requester: Annotated[User, Depends(require_permission("guru:directory"))],
    service: Annotated[KelasService, Depends(get_kelas_service)],
):
    return Envelope(data=service.list_gurus(db, requester))