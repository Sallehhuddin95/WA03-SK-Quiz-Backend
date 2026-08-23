from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tahun import Tahun
from app.models.topic import Topic


class TopicRepository:
    def get_tahun_by_id(self, db: Session, tahun_id: int) -> Tahun | None:
        return db.get(Tahun, tahun_id)

    def list_topics_by_tahun(self, db: Session, tahun_id: int) -> list[Topic]:
        stmt = (
            select(Topic)
            .where(Topic.tahun_id == tahun_id)
            .order_by(Topic.id)
        )
        return list(db.scalars(stmt))