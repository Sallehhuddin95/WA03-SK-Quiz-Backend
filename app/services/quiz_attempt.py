from datetime import datetime

from sqlalchemy.orm import Session

from app.api.deps import KELAS_SCOPE_ALL, KelasScope
from app.core.exceptions import (
    InsufficientQuestionsError,
    InvalidQuestionError,
    NoPermissionError,
    QuizAlreadySubmittedError,
    QuizNotSubmittedError,
    ResourceNotFoundError,
)
from app.core.pagination import normalize_pagination
from app.models.user import User
from app.repositories.question import QuestionRepository
from app.repositories.quiz_attempt import QuizAttemptRepository
from app.schemas.quiz_attempt import (
    AttemptFilterParams,
    AttemptResumeResponse,
    AttemptResultResponse,
    AttemptStartResponse,
    AttemptSummaryResponse,
    QuestionSummaryResponse,
    ResultDetailItemResponse,
    StartAttemptRequest,
    SubmitAttemptRequest,
)
from app.services.grading import grade_answer

JUMLAH_SOALAN = 10
TEKS_SOALAN_PADAM = "Soalan telah dipadam"


class QuizAttemptService:
    def __init__(
        self,
        repository: QuizAttemptRepository,
        question_repository: QuestionRepository,
    ) -> None:
        self._repository = repository
        self._question_repository = question_repository

    def list_attempts(
        self,
        db: Session,
        user: User,
        scope: KelasScope | object,
        filters: AttemptFilterParams,
    ) -> tuple[list[AttemptSummaryResponse], dict]:
        page, page_size = normalize_pagination(
            filters.page, filters.page_size, default_page_size=20
        )
        offset = (page - 1) * page_size

        user_id = None
        kelas_ids = None
        participant_name = filters.participant_name
        if user.role == "murid":
            user_id = user.id
            participant_name = None
        elif scope is not KELAS_SCOPE_ALL:
            kelas_ids = set(scope.visible)

        attempts, total_items = self._repository.list_attempts(
            db,
            topic_id=filters.topic_id,
            difficulty=filters.difficulty,
            participant_name=participant_name,
            status=filters.status,
            user_id=user_id,
            kelas_ids=kelas_ids,
            offset=offset,
            limit=page_size,
        )
        responses = [
            self._to_summary(db, attempt)
            for attempt in attempts
        ]
        meta = {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": (
                (total_items + page_size - 1) // page_size if total_items > 0 else 0
            ),
        }
        return responses, meta

    def start_attempt(
        self, db: Session, user: User, request: StartAttemptRequest
    ) -> AttemptStartResponse:
        self._semak_topik_wujud(db, request.topic_id)
        jumlah_layak = self._question_repository.count_eligible(
            db,
            topic_id=request.topic_id,
            tahap_kesukaran=request.tahap_kesukaran,
        )
        if jumlah_layak < JUMLAH_SOALAN:
            raise InsufficientQuestionsError(
                f"Tidak cukup soalan. Hanya terdapat {jumlah_layak} soalan aktif untuk Topik dan Tahap ini."
            )

        question_ids = self._question_repository.get_eligible_question_ids(
            db,
            topic_id=request.topic_id,
            tahap_kesukaran=request.tahap_kesukaran,
            limit=JUMLAH_SOALAN,
        )
        nama_peserta = f"{user.nama_first} {user.nama_last}".strip()
        attempt = self._repository.create_attempt(
            db,
            topic_id=request.topic_id,
            tahap_kesukaran=request.tahap_kesukaran,
            nama_peserta=nama_peserta,
            jumlah_soalan=JUMLAH_SOALAN,
            user_id=user.id,
        )
        self._repository.create_answers(db, attempt.id, question_ids)
        self._repository.commit_attempt(db)
        db.refresh(attempt)

        questions = self._question_repository.get_questions_by_ids(db, question_ids)
        questions_by_id = {question.id: question for question in questions}
        ordered_questions = [questions_by_id[qid] for qid in question_ids]
        topic_nama = self._repository.get_topic_nama(db, attempt.topic_id) or ""
        return AttemptStartResponse(
            id=attempt.id,
            topic_id=attempt.topic_id,
            topic_nama=topic_nama,
            tahap_kesukaran=attempt.tahap_kesukaran,
            nama_peserta=attempt.nama_peserta,
            status=attempt.status,
            skor=attempt.skor,
            jumlah_soalan=attempt.jumlah_soalan,
            masa_mula=attempt.masa_mula,
            masa_hantar=attempt.masa_hantar,
            soalan=[
                {
                    "id": question.id,
                    "jenis_soalan": question.jenis_soalan,
                    "teks_soalan": question.teks_soalan,
                    "pilihan": question.pilihan,
                }
                for question in ordered_questions
            ],
        )

    def submit_attempt(
        self,
        db: Session,
        user: User,
        attempt_id: int,
        request: SubmitAttemptRequest,
    ) -> AttemptResultResponse:
        attempt = self._repository.get_attempt_by_id(db, attempt_id)
        if attempt is None:
            raise ResourceNotFoundError("Percubaan tidak dijumpai.")
        if attempt.user_id != user.id:
            raise NoPermissionError()
        if attempt.status == "selesai":
            raise QuizAlreadySubmittedError()

        answers_with_questions = self._repository.get_answers_with_questions(
            db, attempt_id
        )
        answer_by_question_id: dict[int, tuple] = {}
        for answer, question in answers_with_questions:
            if answer.question_id is not None:
                answer_by_question_id[answer.question_id] = (answer, question)

        submitted_ids = {item.question_id for item in request.jawapan}
        unknown_ids = submitted_ids - set(answer_by_question_id.keys())
        if unknown_ids:
            raise InvalidQuestionError()

        skor = 0
        for item in request.jawapan:
            answer, question = answer_by_question_id[item.question_id]
            jenis_soalan = question.jenis_soalan if question else ""
            jawapan_betul = question.jawapan_betul if question else None
            adalah_betul = grade_answer(
                jenis_soalan, item.data_jawapan, jawapan_betul
            )
            if adalah_betul:
                skor += 1
            self._repository.update_answer(
                db,
                answer,
                data_jawapan=item.data_jawapan,
                adalah_betul=adalah_betul,
            )

        self._repository.finish_attempt(
            db, attempt, skor=skor, masa_hantar=datetime.now(attempt.masa_mula.tzinfo)
        )
        return self._build_result(db, attempt)

    def get_result(
        self,
        db: Session,
        user: User,
        scope: KelasScope | object,
        attempt_id: int,
        include_questions: bool,
    ) -> AttemptResultResponse | AttemptResumeResponse:
        attempt = self._repository.get_attempt_by_id(db, attempt_id)
        if attempt is None:
            raise ResourceNotFoundError("Percubaan tidak dijumpai.")

        self._semak_boleh_baca_attempt(db, user, scope, attempt)

        if attempt.status == "selesai":
            return self._build_result(db, attempt)
        if include_questions:
            return self._build_resume(db, attempt)
        raise QuizNotSubmittedError()

    def preview_questions(
        self, db: Session, topic_id: int, tahap_kesukaran: str | None
    ) -> list[QuestionSummaryResponse]:
        self._semak_topik_wujud(db, topic_id)
        if tahap_kesukaran is None:
            jumlah_layak = 0
            for tahap in ("mudah", "sederhana", "sukar"):
                jumlah_layak += self._question_repository.count_eligible(
                    db, topic_id=topic_id, tahap_kesukaran=tahap
                )
        else:
            jumlah_layak = self._question_repository.count_eligible(
                db, topic_id=topic_id, tahap_kesukaran=tahap_kesukaran
            )
        if jumlah_layak < JUMLAH_SOALAN:
            raise InsufficientQuestionsError(
                f"Tidak cukup soalan. Hanya terdapat {jumlah_layak} soalan aktif untuk Topik dan Tahap ini."
            )

        question_ids = self._question_repository.get_eligible_question_ids(
            db,
            topic_id=topic_id,
            tahap_kesukaran=tahap_kesukaran,
            limit=JUMLAH_SOALAN,
        )
        questions = self._question_repository.get_questions_by_ids(db, question_ids)
        questions_by_id = {question.id: question for question in questions}
        ordered = [questions_by_id[qid] for qid in question_ids]
        return [
            QuestionSummaryResponse(
                id=question.id,
                jenis_soalan=question.jenis_soalan,
                teks_soalan=question.teks_soalan,
                pilihan=question.pilihan,
            )
            for question in ordered
        ]

    def _semak_boleh_baca_attempt(
        self,
        db: Session,
        user: User,
        scope: KelasScope | object,
        attempt,
    ) -> None:
        if user.role == "murid":
            if attempt.user_id != user.id:
                raise NoPermissionError()
            return
        if scope is KELAS_SCOPE_ALL:
            return
        if attempt.user_id is None:
            raise NoPermissionError()
        murid = attempt.user
        if murid is None or murid.kelas_id is None:
            raise NoPermissionError()
        if murid.kelas_id not in scope.visible:
            raise NoPermissionError()

    def _build_result(self, db: Session, attempt) -> AttemptResultResponse:
        answers_with_questions = self._repository.get_answers_with_questions(
            db, attempt.id
        )
        topic_nama = self._repository.get_topic_nama(db, attempt.topic_id) or ""
        perincian: list[ResultDetailItemResponse] = []
        for answer, question in answers_with_questions:
            if question is None:
                perincian.append(
                    ResultDetailItemResponse(
                        question_id=answer.question_id,
                        jenis_soalan="",
                        teks_soalan=TEKS_SOALAN_PADAM,
                        pilihan=None,
                        jawapan_murid=answer.data_jawapan,
                        jawapan_betul=None,
                        adalah_betul=answer.adalah_betul,
                    )
                )
            else:
                perincian.append(
                    ResultDetailItemResponse(
                        question_id=question.id,
                        jenis_soalan=question.jenis_soalan,
                        teks_soalan=question.teks_soalan,
                        pilihan=question.pilihan,
                        jawapan_murid=answer.data_jawapan,
                        jawapan_betul=question.jawapan_betul,
                        adalah_betul=answer.adalah_betul,
                    )
                )
        return AttemptResultResponse(
            id=attempt.id,
            topic_id=attempt.topic_id,
            topic_nama=topic_nama,
            tahap_kesukaran=attempt.tahap_kesukaran,
            nama_peserta=attempt.nama_peserta,
            status=attempt.status,
            skor=attempt.skor,
            jumlah_soalan=attempt.jumlah_soalan,
            masa_mula=attempt.masa_mula,
            masa_hantar=attempt.masa_hantar,
            perincian=perincian,
        )

    def _build_resume(self, db: Session, attempt) -> AttemptResumeResponse:
        answers_with_questions = self._repository.get_answers_with_questions(
            db, attempt.id
        )
        topic_nama = self._repository.get_topic_nama(db, attempt.topic_id) or ""
        soalan = []
        for answer, question in answers_with_questions:
            if question is None:
                soalan.append(
                    {
                        "id": answer.question_id,
                        "jenis_soalan": "",
                        "teks_soalan": TEKS_SOALAN_PADAM,
                        "pilihan": None,
                    }
                )
            else:
                soalan.append(
                    {
                        "id": question.id,
                        "jenis_soalan": question.jenis_soalan,
                        "teks_soalan": question.teks_soalan,
                        "pilihan": question.pilihan,
                    }
                )
        return AttemptResumeResponse(
            id=attempt.id,
            topic_id=attempt.topic_id,
            topic_nama=topic_nama,
            tahap_kesukaran=attempt.tahap_kesukaran,
            nama_peserta=attempt.nama_peserta,
            status=attempt.status,
            skor=attempt.skor,
            jumlah_soalan=attempt.jumlah_soalan,
            masa_mula=attempt.masa_mula,
            masa_hantar=attempt.masa_hantar,
            soalan=soalan,
        )

    def _to_summary(self, db: Session, attempt) -> AttemptSummaryResponse:
        topic_nama = self._repository.get_topic_nama(db, attempt.topic_id) or ""
        return AttemptSummaryResponse(
            id=attempt.id,
            topic_id=attempt.topic_id,
            topic_nama=topic_nama,
            tahap_kesukaran=attempt.tahap_kesukaran,
            nama_peserta=attempt.nama_peserta,
            status=attempt.status,
            skor=attempt.skor,
            jumlah_soalan=attempt.jumlah_soalan,
            masa_mula=attempt.masa_mula,
            masa_hantar=attempt.masa_hantar,
            created_at=attempt.created_at,
            updated_at=attempt.updated_at,
        )

    def _semak_topik_wujud(self, db: Session, topic_id: int) -> None:
        if self._repository.get_topic_nama(db, topic_id) is None:
            raise ResourceNotFoundError("Topik tidak dijumpai.")