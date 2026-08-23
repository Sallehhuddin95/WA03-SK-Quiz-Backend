from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.question import QuestionRepository
from app.repositories.quiz_attempt import QuizAttemptRepository
from app.schemas.common import Envelope, PaginatedEnvelope
from app.schemas.quiz_attempt import (
    AttemptFilterParams,
    AttemptResumeResponse,
    AttemptResultResponse,
    AttemptStartResponse,
    AttemptSummaryResponse,
    StartAttemptRequest,
    SubmitAttemptRequest,
)
from app.services.quiz_attempt import QuizAttemptService

router = APIRouter(prefix="/quiz-attempts", tags=["quiz-attempts"])

DbSession = Annotated[Session, Depends(get_db)]


def get_quiz_attempt_service() -> QuizAttemptService:
    return QuizAttemptService(QuizAttemptRepository(), QuestionRepository())


@router.get("", response_model=PaginatedEnvelope[AttemptSummaryResponse])
def list_attempts(
    db: DbSession,
    service: Annotated[QuizAttemptService, Depends(get_quiz_attempt_service)],
    topic_id: Annotated[int | None, Query()] = None,
    difficulty: Annotated[str | None, Query()] = None,
    participant_name: Annotated[str | None, Query()] = None,
    attempt_status: Annotated[str | None, Query(alias="status")] = None,
    page: Annotated[int | None, Query()] = None,
    page_size: Annotated[int | None, Query()] = None,
):
    filters = AttemptFilterParams(
        topic_id=topic_id,
        difficulty=difficulty,
        participant_name=participant_name,
        status=attempt_status,
        page=page,
        page_size=page_size,
    )
    data, meta = service.list_attempts(db, filters)
    return PaginatedEnvelope(data=data, meta=meta)


@router.post(
    "",
    response_model=Envelope[AttemptStartResponse],
    status_code=status.HTTP_201_CREATED,
)
def start_attempt(
    payload: StartAttemptRequest,
    db: DbSession,
    service: Annotated[QuizAttemptService, Depends(get_quiz_attempt_service)],
):
    return Envelope(data=service.start_attempt(db, payload))


@router.post(
    "/{attempt_id}/submit",
    response_model=Envelope[AttemptResultResponse],
)
def submit_attempt(
    attempt_id: int,
    payload: SubmitAttemptRequest,
    db: DbSession,
    service: Annotated[QuizAttemptService, Depends(get_quiz_attempt_service)],
):
    return Envelope(data=service.submit_attempt(db, attempt_id, payload))


@router.get(
    "/{attempt_id}/result",
    response_model=Envelope[AttemptResultResponse | AttemptResumeResponse],
)
def get_attempt_result(
    attempt_id: int,
    db: DbSession,
    service: Annotated[QuizAttemptService, Depends(get_quiz_attempt_service)],
    include_questions: Annotated[bool, Query()] = False,
):
    result = service.get_result(db, attempt_id, include_questions=include_questions)
    return Envelope(data=result)