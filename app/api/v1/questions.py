from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.repositories.question import QuestionRepository
from app.schemas.common import Envelope, PaginatedEnvelope
from app.schemas.question import (
    BulkQuestionDeleteSummary,
    BulkQuestionIdsRequest,
    BulkQuestionStatusRequest,
    BulkQuestionStatusSummary,
    CreateQuestionRequest,
    QuestionFilterParams,
    QuestionResponse,
    UpdateQuestionRequest,
    UpdateQuestionStatusRequest,
)
from app.services.question import QuestionService

router = APIRouter(prefix="/questions", tags=["questions"])

DbSession = Annotated[Session, Depends(get_db)]


def get_question_service() -> QuestionService:
    return QuestionService(QuestionRepository())


@router.get("", response_model=PaginatedEnvelope[QuestionResponse])
def list_questions(
    db: DbSession,
    service: Annotated[QuestionService, Depends(get_question_service)],
    staff: Annotated[User, Depends(require_permission("question:manage"))],
    topic_id: Annotated[int | None, Query()] = None,
    difficulty: Annotated[str | None, Query()] = None,
    question_type: Annotated[str | None, Query()] = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    page: Annotated[int | None, Query()] = None,
    page_size: Annotated[int | None, Query()] = None,
):
    filters = QuestionFilterParams(
        topic_id=topic_id,
        difficulty=difficulty,
        question_type=question_type,
        status=status_filter,
        page=page,
        page_size=page_size,
    )
    data, meta = service.list_questions(db, filters)
    return PaginatedEnvelope(data=data, meta=meta)


@router.get(
    "/{question_id}",
    response_model=Envelope[QuestionResponse],
)
def get_question(
    question_id: int,
    db: DbSession,
    service: Annotated[QuestionService, Depends(get_question_service)],
    staff: Annotated[User, Depends(require_permission("question:manage"))],
):
    return Envelope(data=service.get_question(db, question_id))


@router.post(
    "",
    response_model=Envelope[QuestionResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_question(
    payload: CreateQuestionRequest,
    db: DbSession,
    service: Annotated[QuestionService, Depends(get_question_service)],
    staff: Annotated[User, Depends(require_permission("question:manage"))],
):
    return Envelope(data=service.create_question(db, payload))


@router.put(
    "/{question_id}",
    response_model=Envelope[QuestionResponse],
)
def update_question(
    question_id: int,
    payload: UpdateQuestionRequest,
    db: DbSession,
    service: Annotated[QuestionService, Depends(get_question_service)],
    staff: Annotated[User, Depends(require_permission("question:manage"))],
):
    return Envelope(data=service.update_question(db, question_id, payload))


@router.delete("/{question_id}")
def delete_question(
    question_id: int,
    db: DbSession,
    service: Annotated[QuestionService, Depends(get_question_service)],
    staff: Annotated[User, Depends(require_permission("question:manage"))],
):
    return Envelope(data=service.delete_question(db, question_id))


@router.patch(
    "/{question_id}/status",
    response_model=Envelope[QuestionResponse],
)
def update_question_status(
    question_id: int,
    payload: UpdateQuestionStatusRequest,
    db: DbSession,
    service: Annotated[QuestionService, Depends(get_question_service)],
    staff: Annotated[User, Depends(require_permission("question:manage"))],
):
    return Envelope(data=service.update_question_status(db, question_id, payload))


@router.post(
    "/bulk-delete",
    response_model=Envelope[BulkQuestionDeleteSummary],
)
def bulk_delete_questions(
    payload: BulkQuestionIdsRequest,
    db: DbSession,
    service: Annotated[QuestionService, Depends(get_question_service)],
    staff: Annotated[User, Depends(require_permission("question:manage"))],
):
    return Envelope(data=service.bulk_delete(db, payload.ids))


@router.post(
    "/bulk-status",
    response_model=Envelope[BulkQuestionStatusSummary],
)
def bulk_update_questions_status(
    payload: BulkQuestionStatusRequest,
    db: DbSession,
    service: Annotated[QuestionService, Depends(get_question_service)],
    staff: Annotated[User, Depends(require_permission("question:manage"))],
):
    return Envelope(data=service.bulk_update_status(db, payload))