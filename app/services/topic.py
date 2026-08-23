from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError
from app.repositories.topic import TopicRepository
from app.schemas.topic import TopicResponse


class TopicService:
    def __init__(self, repository: TopicRepository) -> None:
        self._repository = repository

    def list_topics_by_tahun(self, db: Session, tahun_id: int) -> list[TopicResponse]:
        tahun = self._repository.get_tahun_by_id(db, tahun_id)
        if tahun is None:
            raise ResourceNotFoundError("Tahun tidak dijumpai.")
        topics = self._repository.list_topics_by_tahun(db, tahun_id)
        return [
            TopicResponse.model_validate(topic)
            for topic in topics
        ]