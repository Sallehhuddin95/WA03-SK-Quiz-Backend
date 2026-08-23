from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.topic import TopicRepository
from app.schemas.common import Envelope
from app.schemas.topic import TopicResponse
from app.services.topic import TopicService

router = APIRouter(prefix="/tahun", tags=["topics"])

DbSession = Annotated[Session, Depends(get_db)]


def get_topic_service() -> TopicService:
    return TopicService(TopicRepository())


@router.get("/{tahun_id}/topics", response_model=Envelope[list[TopicResponse]])
def list_topics_by_tahun(
    tahun_id: int,
    db: DbSession,
    service: Annotated[TopicService, Depends(get_topic_service)],
):
    return Envelope(data=service.list_topics_by_tahun(db, tahun_id))