from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.question import Question
from app.models.topic import Topic


class QuestionRepository:
    def list_questions(
        self,
        db: Session,
        *,
        topic_id: int | None,
        difficulty: str | None,
        question_type: str | None,
        status: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Question], int]:
        filters = []
        if topic_id is not None:
            filters.append(Question.topic_id == topic_id)
        if difficulty is not None:
            filters.append(Question.tahap_kesukaran == difficulty)
        if question_type is not None:
            filters.append(Question.jenis_soalan == question_type)
        if status is not None:
            filters.append(Question.status == status)

        count_stmt = select(func.count()).select_from(Question).where(*filters)
        total_items = db.scalar(count_stmt) or 0

        stmt = (
            select(Question)
            .where(*filters)
            .order_by(Question.id)
            .offset(offset)
            .limit(limit)
        )
        return list(db.scalars(stmt)), total_items

    def get_question_by_id(self, db: Session, question_id: int) -> Question | None:
        return db.get(Question, question_id)

    def create_question(
        self,
        db: Session,
        *,
        topic_id: int,
        jenis_soalan: str,
        tahap_kesukaran: str,
        status: str,
        teks_soalan: str,
        pilihan: dict | None,
        jawapan_betul: dict,
    ) -> Question:
        question = Question(
            topic_id=topic_id,
            jenis_soalan=jenis_soalan,
            tahap_kesukaran=tahap_kesukaran,
            status=status,
            teks_soalan=teks_soalan,
            pilihan=pilihan,
            jawapan_betul=jawapan_betul,
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        return question

    def update_question(self, db: Session, question: Question, **changes) -> Question:
        for field, value in changes.items():
            setattr(question, field, value)
        db.commit()
        db.refresh(question)
        return question

    def delete_question(self, db: Session, question: Question) -> None:
        db.delete(question)
        db.commit()

    def count_active(
        self,
        db: Session,
        *,
        topic_id: int,
        jenis_soalan: str,
        tahap_kesukaran: str,
        exclude_id: int | None = None,
    ) -> int:
        filters = [
            Question.topic_id == topic_id,
            Question.jenis_soalan == jenis_soalan,
            Question.tahap_kesukaran == tahap_kesukaran,
            Question.status == "aktif",
        ]
        if exclude_id is not None:
            filters.append(Question.id != exclude_id)
        stmt = select(func.count()).select_from(Question).where(*filters)
        return db.scalar(stmt) or 0

    def get_topic_nama(self, db: Session, topic_id: int) -> str | None:
        return db.scalar(select(Topic.nama).where(Topic.id == topic_id))

    def get_eligible_question_ids(
        self, db: Session, *, topic_id: int, tahap_kesukaran: str, limit: int
    ) -> list[int]:
        stmt = (
            select(Question.id)
            .where(
                Question.topic_id == topic_id,
                Question.tahap_kesukaran == tahap_kesukaran,
                Question.status == "aktif",
            )
            .order_by(func.random())
            .limit(limit)
        )
        return list(db.scalars(stmt))

    def count_eligible(
        self, db: Session, *, topic_id: int, tahap_kesukaran: str
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Question)
            .where(
                Question.topic_id == topic_id,
                Question.tahap_kesukaran == tahap_kesukaran,
                Question.status == "aktif",
            )
        )
        return db.scalar(stmt) or 0

    def get_questions_by_ids(
        self, db: Session, question_ids: list[int]
    ) -> list[Question]:
        stmt = select(Question).where(Question.id.in_(question_ids))
        return list(db.scalars(stmt))