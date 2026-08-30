from sqlalchemy.orm import Session

from app.core.exceptions import (
    FillBlankMarkerMissingError,
    QuestionLimitReachedError,
    ResourceNotFoundError,
)
from app.core.pagination import normalize_pagination
from app.models.question import Question
from app.repositories.question import QuestionRepository
from app.schemas.question import (
    PENANDA_TEMPAT_KOSONG,
    BulkQuestionDeleteSummary,
    BulkQuestionStatusRequest,
    BulkQuestionStatusSummary,
    CreateQuestionRequest,
    QuestionFilterParams,
    QuestionResponse,
    UpdateQuestionRequest,
    UpdateQuestionStatusRequest,
    _sahkan_aneka_pilihan,
    _sahkan_betul_salah,
    _sahkan_isi_tempat_kosong,
    _sahkan_padanan,
)

HAD_AKTIF = 10


class QuestionService:
    def __init__(self, repository: QuestionRepository) -> None:
        self._repository = repository

    def list_questions(
        self, db: Session, filters: QuestionFilterParams
    ) -> tuple[list[QuestionResponse], dict]:
        page, page_size = normalize_pagination(filters.page, filters.page_size)
        offset = (page - 1) * page_size
        questions, total_items = self._repository.list_questions(
            db,
            topic_id=filters.topic_id,
            difficulty=filters.difficulty,
            question_type=filters.question_type,
            status=filters.status,
            offset=offset,
            limit=page_size,
        )
        responses = [
            self._to_response(db, question)
            for question in questions
        ]
        meta = {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": (total_items + page_size - 1) // page_size if total_items > 0 else 0,
        }
        return responses, meta

    def get_question(self, db: Session, question_id: int) -> QuestionResponse:
        question = self._repository.get_question_by_id(db, question_id)
        if question is None:
            raise ResourceNotFoundError("Soalan tidak dijumpai.")
        return self._to_response(db, question)

    def create_question(
        self, db: Session, request: CreateQuestionRequest
    ) -> QuestionResponse:
        self._semak_topik_wujud(db, request.topic_id)
        if request.status == "aktif":
            self._semak_had_aktif(
                db,
                topic_id=request.topic_id,
                jenis_soalan=request.jenis_soalan,
                tahap_kesukaran=request.tahap_kesukaran,
            )
        self._semak_penanda_tempat_kosong(
            request.jenis_soalan, request.teks_soalan
        )
        question = self._repository.create_question(
            db,
            topic_id=request.topic_id,
            jenis_soalan=request.jenis_soalan,
            tahap_kesukaran=request.tahap_kesukaran,
            status=request.status,
            teks_soalan=request.teks_soalan,
            pilihan=request.pilihan,
            jawapan_betul=request.jawapan_betul,
        )
        return self._to_response(db, question)

    def update_question(
        self, db: Session, question_id: int, request: UpdateQuestionRequest
    ) -> QuestionResponse:
        question = self._repository.get_question_by_id(db, question_id)
        if question is None:
            raise ResourceNotFoundError("Soalan tidak dijumpai.")

        jenis_soalan = question.jenis_soalan
        self._sahkan_struktur_ikut_jenis(
            jenis_soalan, request.pilihan, request.jawapan_betul
        )
        self._semak_penanda_tempat_kosong(jenis_soalan, request.teks_soalan)
        self._semak_topik_wujud(db, request.topic_id)

        if request.status == "aktif" and question.status != "aktif":
            self._semak_had_aktif(
                db,
                topic_id=request.topic_id,
                jenis_soalan=jenis_soalan,
                tahap_kesukaran=request.tahap_kesukaran,
                exclude_id=question.id,
            )

        updated = self._repository.update_question(
            db,
            question,
            topic_id=request.topic_id,
            tahap_kesukaran=request.tahap_kesukaran,
            status=request.status,
            teks_soalan=request.teks_soalan,
            pilihan=request.pilihan,
            jawapan_betul=request.jawapan_betul,
        )
        return self._to_response(db, updated)

    def delete_question(
        self, db: Session, question_id: int
    ) -> dict[str, str]:
        question = self._repository.get_question_by_id(db, question_id)
        if question is None:
            raise ResourceNotFoundError("Soalan tidak dijumpai.")
        self._repository.delete_question(db, question)
        return {"mesej": "Soalan berjaya dipadam."}

    def update_question_status(
        self, db: Session, question_id: int, request: UpdateQuestionStatusRequest
    ) -> QuestionResponse:
        question = self._repository.get_question_by_id(db, question_id)
        if question is None:
            raise ResourceNotFoundError("Soalan tidak dijumpai.")

        if request.status == "aktif" and question.status != "aktif":
            self._semak_had_aktif(
                db,
                topic_id=question.topic_id,
                jenis_soalan=question.jenis_soalan,
                tahap_kesukaran=question.tahap_kesukaran,
                exclude_id=question.id,
            )

        updated = self._repository.update_question(db, question, status=request.status)
        return self._to_response(db, updated)

    def bulk_delete(self, db: Session, question_ids: list[int]) -> BulkQuestionDeleteSummary:
        questions = self._repository.get_questions_by_ids(db, question_ids)
        found_ids = [question.id for question in questions]
        deleted = self._repository.delete_questions_by_ids(db, found_ids)
        return BulkQuestionDeleteSummary(
            mesej=f"{deleted} soalan berjaya dipadam.",
            dipadam=deleted,
        )

    def bulk_update_status(
        self, db: Session, request: BulkQuestionStatusRequest
    ) -> BulkQuestionStatusSummary:
        questions = self._repository.get_questions_by_ids(db, request.ids)
        self._semak_had_aktif_batch(db, questions, request.status)
        change_ids = [question.id for question in questions if question.status != request.status]
        updated = 0
        if change_ids:
            updated = self._repository.update_questions_status_by_ids(
                db, change_ids, request.status
            )
        return BulkQuestionStatusSummary(
            mesej=f"{updated} soalan berjaya dikemaskini.",
            dikemaskini=updated,
            status=request.status,
        )

    def _semak_had_aktif_batch(
        self, db: Session, questions: list[Question], status: str
    ) -> None:
        """Reject the whole batch if activating any group would exceed HAD_AKTIF.

        Activation is only a risk when the target status is "aktif". Questions
        that are already active stay in the count; questions switching from
        inactive to active add to it. The guard runs before any write, so a
        failing batch leaves everything untouched (atomic reject).
        """
        if status != "aktif":
            return
        groups: dict[tuple[int, str, str], list[Question]] = {}
        for question in questions:
            if question.status == "aktif":
                continue
            key = (question.topic_id, question.jenis_soalan, question.tahap_kesukaran)
            groups.setdefault(key, []).append(question)
        for (topic_id, jenis_soalan, tahap_kesukaran), batch_questions in groups.items():
            count = self._repository.count_active(
                db,
                topic_id=topic_id,
                jenis_soalan=jenis_soalan,
                tahap_kesukaran=tahap_kesukaran,
            )
            if count + len(batch_questions) > HAD_AKTIF:
                raise QuestionLimitReachedError()

    def _to_response(self, db: Session, question: Question) -> QuestionResponse:
        topic_nama = self._repository.get_topic_nama(db, question.topic_id) or ""
        return QuestionResponse(
            id=question.id,
            topic_id=question.topic_id,
            topic_nama=topic_nama,
            jenis_soalan=question.jenis_soalan,
            tahap_kesukaran=question.tahap_kesukaran,
            status=question.status,
            teks_soalan=question.teks_soalan,
            pilihan=question.pilihan,
            jawapan_betul=question.jawapan_betul,
            created_at=question.created_at,
            updated_at=question.updated_at,
        )

    def _semak_topik_wujud(self, db: Session, topic_id: int) -> None:
        if self._repository.get_topic_nama(db, topic_id) is None:
            raise ResourceNotFoundError("Topik tidak dijumpai.")

    def _semak_had_aktif(
        self,
        db: Session,
        *,
        topic_id: int,
        jenis_soalan: str,
        tahap_kesukaran: str,
        exclude_id: int | None = None,
    ) -> None:
        count = self._repository.count_active(
            db,
            topic_id=topic_id,
            jenis_soalan=jenis_soalan,
            tahap_kesukaran=tahap_kesukaran,
            exclude_id=exclude_id,
        )
        if count >= HAD_AKTIF:
            raise QuestionLimitReachedError()

    def _semak_penanda_tempat_kosong(
        self, jenis_soalan: str, teks_soalan: str
    ) -> None:
        if jenis_soalan == "isi_tempat_kosong" and PENANDA_TEMPAT_KOSONG not in teks_soalan:
            raise FillBlankMarkerMissingError()

    def _sahkan_struktur_ikut_jenis(
        self,
        jenis_soalan: str,
        pilihan: dict[str, str] | None,
        jawapan_betul: dict,
    ) -> None:
        if jenis_soalan == "aneka_pilihan":
            _sahkan_aneka_pilihan(pilihan, jawapan_betul)
        elif jenis_soalan == "isi_tempat_kosong":
            _sahkan_isi_tempat_kosong(pilihan, jawapan_betul)
        elif jenis_soalan == "betul_salah":
            _sahkan_betul_salah(pilihan, jawapan_betul)
        elif jenis_soalan == "padanan":
            _sahkan_padanan(pilihan, jawapan_betul)