from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError
from app.repositories.subject import SubjectRepository
from app.schemas.subject import SubjectResponse, TahunResponse


class SubjectService:
    def __init__(self, repository: SubjectRepository) -> None:
        self._repository = repository

    def list_subjects(self, db: Session) -> list[SubjectResponse]:
        subjects = self._repository.list_subjects(db)
        return [
            SubjectResponse.model_validate(subject)
            for subject in subjects
        ]

    def list_tahun_by_subject(self, db: Session, subject_id: int) -> list[TahunResponse]:
        subject = self._repository.get_subject_by_id(db, subject_id)
        if subject is None:
            raise ResourceNotFoundError("Mata pelajaran tidak dijumpai.")
        tahun_list = self._repository.list_tahun_by_subject(db, subject_id)
        return [
            TahunResponse.model_validate(tahun)
            for tahun in tahun_list
        ]