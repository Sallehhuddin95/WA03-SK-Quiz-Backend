from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.repositories.question import QuestionRepository
from app.repositories.quiz_attempt import QuizAttemptRepository
from app.schemas.common import Envelope
from app.schemas.question import Difficulty
from app.schemas.quiz_attempt import QuestionSummaryResponse
from app.services.quiz_attempt import QuizAttemptService

router = APIRouter(prefix="/kuiz", tags=["kuiz"])

DbSession = Annotated[Session, Depends(get_db)]


def get_quiz_attempt_service() -> QuizAttemptService:
    return QuizAttemptService(QuizAttemptRepository(), QuestionRepository())


@router.get("/pratonton", response_model=Envelope[list[QuestionSummaryResponse]])
def preview_questions(
    db: DbSession,
    service: Annotated[QuizAttemptService, Depends(get_quiz_attempt_service)],
    staff: Annotated[User, Depends(require_permission("attempt:preview"))],
    topic_id: Annotated[int, Query(gt=0)],
    tahap_kesukaran: Annotated[Difficulty | None, Query()] = None,
):
    return Envelope(data=service.preview_questions(db, topic_id, tahap_kesukaran))