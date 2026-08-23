from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.models.tahun import Tahun


class SubjectRepository:
    def list_subjects(self, db: Session) -> list[Subject]:
        stmt = select(Subject).order_by(Subject.id)
        return list(db.scalars(stmt))

    def get_subject_by_id(self, db: Session, subject_id: int) -> Subject | None:
        return db.get(Subject, subject_id)

    def list_tahun_by_subject(self, db: Session, subject_id: int) -> list[Tahun]:
        stmt = (
            select(Tahun)
            .where(Tahun.subject_id == subject_id)
            .order_by(Tahun.id)
        )
        return list(db.scalars(stmt))