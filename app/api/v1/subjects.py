from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.repositories.subject import SubjectRepository
from app.schemas.common import Envelope
from app.schemas.subject import SubjectResponse, TahunResponse
from app.services.subject import SubjectService

router = APIRouter(prefix="/subjects", tags=["subjects"])

DbSession = Annotated[Session, Depends(get_db)]


def get_subject_service() -> SubjectService:
    return SubjectService(SubjectRepository())


@router.get("", response_model=Envelope[list[SubjectResponse]])
def list_subjects(
    db: DbSession,
    service: Annotated[SubjectService, Depends(get_subject_service)],
    user: Annotated[User, Depends(require_permission("reference:read"))],
):
    return Envelope(data=service.list_subjects(db))


@router.get("/{subject_id}/tahun", response_model=Envelope[list[TahunResponse]])
def list_tahun_by_subject(
    subject_id: int,
    db: DbSession,
    service: Annotated[SubjectService, Depends(get_subject_service)],
    user: Annotated[User, Depends(require_permission("reference:read"))],
):
    return Envelope(data=service.list_tahun_by_subject(db, subject_id))