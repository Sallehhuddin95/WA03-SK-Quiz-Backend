from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.question import Question
from app.models.quiz_answer import QuizAnswer
from app.models.quiz_attempt import QuizAttempt
from app.models.topic import Topic


class QuizAttemptRepository:
    def list_attempts(
        self,
        db: Session,
        *,
        topic_id: int | None,
        difficulty: str | None,
        participant_name: str | None,
        status: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[QuizAttempt], int]:
        filters = []
        if topic_id is not None:
            filters.append(QuizAttempt.topic_id == topic_id)
        if difficulty is not None:
            filters.append(QuizAttempt.tahap_kesukaran == difficulty)
        if participant_name:
            filters.append(QuizAttempt.nama_peserta.ilike(f"%{participant_name}%"))
        if status is not None:
            filters.append(QuizAttempt.status == status)

        count_stmt = (
            select(func.count())
            .select_from(QuizAttempt)
            .where(*filters)
        )
        total_items = db.scalar(count_stmt) or 0

        stmt = (
            select(QuizAttempt)
            .where(*filters)
            .order_by(QuizAttempt.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(db.scalars(stmt)), total_items

    def get_attempt_by_id(self, db: Session, attempt_id: int) -> QuizAttempt | None:
        return db.get(QuizAttempt, attempt_id)

    def create_attempt(
        self,
        db: Session,
        *,
        topic_id: int,
        tahap_kesukaran: str,
        nama_peserta: str,
        jumlah_soalan: int,
    ) -> QuizAttempt:
        attempt = QuizAttempt(
            topic_id=topic_id,
            tahap_kesukaran=tahap_kesukaran,
            nama_peserta=nama_peserta,
            status="dalam_progres",
            skor=None,
            jumlah_soalan=jumlah_soalan,
        )
        db.add(attempt)
        db.flush()
        return attempt

    def create_answers(
        self, db: Session, attempt_id: int, question_ids: list[int]
    ) -> list[QuizAnswer]:
        answers = [
            QuizAnswer(
                quiz_attempt_id=attempt_id,
                question_id=question_id,
                data_jawapan=None,
                adalah_betul=None,
            )
            for question_id in question_ids
        ]
        db.add_all(answers)
        db.flush()
        return answers

    def get_answers_with_questions(
        self, db: Session, attempt_id: int
    ) -> list[tuple[QuizAnswer, Question | None]]:
        stmt = (
            select(QuizAnswer, Question)
            .outerjoin(Question, QuizAnswer.question_id == Question.id)
            .where(QuizAnswer.quiz_attempt_id == attempt_id)
            .order_by(QuizAnswer.id)
        )
        return list(db.execute(stmt))

    def update_answer(
        self,
        db: Session,
        answer: QuizAnswer,
        *,
        data_jawapan: dict,
        adalah_betul: bool,
    ) -> None:
        answer.data_jawapan = data_jawapan
        answer.adalah_betul = adalah_betul
        db.flush()

    def finish_attempt(
        self,
        db: Session,
        attempt: QuizAttempt,
        *,
        skor: int,
        masa_hantar: datetime,
    ) -> None:
        attempt.status = "selesai"
        attempt.skor = skor
        attempt.masa_hantar = masa_hantar
        db.commit()

    def commit_attempt(self, db: Session) -> None:
        db.commit()

    def get_topic_nama(self, db: Session, topic_id: int) -> str | None:
        return db.scalar(select(Topic.nama).where(Topic.id == topic_id))