from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.question import Difficulty


class StartAttemptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_id: int = Field(gt=0)
    tahap_kesukaran: Difficulty


class AnswerItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: int = Field(gt=0)
    data_jawapan: dict[str, Any]


class SubmitAttemptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jawapan: list[AnswerItemRequest] = Field(min_length=10, max_length=10)

    @model_validator(mode="after")
    def question_id_unik(self) -> "SubmitAttemptRequest":
        ids = [item.question_id for item in self.jawapan]
        if len(ids) != len(set(ids)):
            raise ValueError("Setiap question_id mesti unik dalam senarai jawapan.")
        return self


class QuestionSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    jenis_soalan: str
    teks_soalan: str
    pilihan: dict[str, str] | None


class AttemptStartResponse(BaseModel):
    id: int
    topic_id: int
    topic_nama: str
    tahap_kesukaran: str
    nama_peserta: str
    status: str
    skor: int | None
    jumlah_soalan: int
    masa_mula: datetime
    masa_hantar: datetime | None
    soalan: list[QuestionSummaryResponse]


class AttemptSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    topic_nama: str
    tahap_kesukaran: str
    nama_peserta: str
    status: str
    skor: int | None
    jumlah_soalan: int
    masa_mula: datetime
    masa_hantar: datetime | None
    created_at: datetime
    updated_at: datetime


class ResultDetailItemResponse(BaseModel):
    question_id: int | None
    jenis_soalan: str
    teks_soalan: str
    pilihan: dict[str, str] | None
    jawapan_murid: dict[str, Any] | None
    jawapan_betul: dict[str, Any] | None
    adalah_betul: bool | None


class AttemptResultResponse(BaseModel):
    id: int
    topic_id: int
    topic_nama: str
    tahap_kesukaran: str
    nama_peserta: str
    status: str
    skor: int | None
    jumlah_soalan: int
    masa_mula: datetime
    masa_hantar: datetime | None
    perincian: list[ResultDetailItemResponse]


class AttemptResumeResponse(BaseModel):
    id: int
    topic_id: int
    topic_nama: str
    tahap_kesukaran: str
    nama_peserta: str
    status: str
    skor: int | None
    jumlah_soalan: int
    masa_mula: datetime
    masa_hantar: datetime | None
    soalan: list[QuestionSummaryResponse]


class AttemptFilterParams(BaseModel):
    topic_id: int | None = None
    difficulty: Difficulty | None = None
    participant_name: str | None = None
    status: str | None = None
    page: int | None = None
    page_size: int | None = None