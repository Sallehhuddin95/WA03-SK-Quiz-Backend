from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

QuestionType = Literal["aneka_pilihan", "isi_tempat_kosong", "betul_salah", "padanan"]
Difficulty = Literal["mudah", "sederhana", "sukar"]
QuestionStatus = Literal["aktif", "tidak_aktif"]

PILIHAN_KUNCI = ("A", "B", "C", "D")
PENANDA_TEMPAT_KOSONG = "______"
MIN_PASANGAN = 2
MAX_PASANGAN = 6
MIN_JAWAPAN_DITERIMA = 1
MAX_JAWAPAN_DITERIMA = 10


class CreateQuestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_id: int = Field(gt=0)
    jenis_soalan: QuestionType
    tahap_kesukaran: Difficulty
    status: QuestionStatus = "aktif"
    teks_soalan: str = Field(min_length=5, max_length=500)
    pilihan: dict[str, str] | None = None
    jawapan_betul: dict[str, Any]

    @field_validator("teks_soalan")
    @classmethod
    def teks_soalan_tidak_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Teks soalan tidak boleh kosong.")
        return value

    @model_validator(mode="after")
    def sahkan_mengikut_jenis(self) -> "CreateQuestionRequest":
        jenis = self.jenis_soalan
        if jenis == "aneka_pilihan":
            _sahkan_aneka_pilihan(self.pilihan, self.jawapan_betul)
        elif jenis == "isi_tempat_kosong":
            _sahkan_isi_tempat_kosong(self.pilihan, self.jawapan_betul)
        elif jenis == "betul_salah":
            _sahkan_betul_salah(self.pilihan, self.jawapan_betul)
        elif jenis == "padanan":
            _sahkan_padanan(self.pilihan, self.jawapan_betul)
        return self


class UpdateQuestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_id: int = Field(gt=0)
    jenis_soalan: QuestionType | None = None
    tahap_kesukaran: Difficulty
    status: QuestionStatus = "aktif"
    teks_soalan: str = Field(min_length=5, max_length=500)
    pilihan: dict[str, str] | None = None
    jawapan_betul: dict[str, Any]

    @field_validator("teks_soalan")
    @classmethod
    def teks_soalan_tidak_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Teks soalan tidak boleh kosong.")
        return value


class UpdateQuestionStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: QuestionStatus


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    topic_nama: str
    jenis_soalan: str
    tahap_kesukaran: str
    status: str
    teks_soalan: str
    pilihan: dict[str, str] | None
    jawapan_betul: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class QuestionFilterParams(BaseModel):
    topic_id: int | None = None
    difficulty: Difficulty | None = None
    question_type: QuestionType | None = None
    status: QuestionStatus | None = None
    page: int | None = None
    page_size: int | None = None


def _sahkan_aneka_pilihan(
    pilihan: dict[str, str] | None,
    jawapan_betul: dict[str, Any],
) -> None:
    if pilihan is None:
        raise ValueError("Pilihan A, B, C, D wajib untuk soalan aneka pilihan.")
    for kunci in PILIHAN_KUNCI:
        if kunci not in pilihan or not str(pilihan[kunci]).strip():
            raise ValueError(f"Pilihan {kunci} wajib diisi.")
    if set(jawapan_betul.keys()) != {"pilihan"}:
        raise ValueError("jawapan_betul mesti berbentuk {\"pilihan\": \"A\"}.")
    nilai = jawapan_betul.get("pilihan")
    if nilai not in PILIHAN_KUNCI:
        raise ValueError("jawapan_betul.pilihan mesti salah satu daripada A, B, C, atau D.")


def _sahkan_isi_tempat_kosong(
    pilihan: dict[str, str] | None,
    jawapan_betul: dict[str, Any],
) -> None:
    if pilihan is not None:
        raise ValueError("pilihan mesti null untuk soalan isi tempat kosong.")
    if set(jawapan_betul.keys()) != {"jawapan_diterima"}:
        raise ValueError("jawapan_betul mesti berbentuk {\"jawapan_diterima\": [...]}.")
    senarai = jawapan_betul.get("jawapan_diterima")
    if not isinstance(senarai, list):
        raise ValueError("jawapan_diterima mesti senarai jawapan.")
    if not (MIN_JAWAPAN_DITERIMA <= len(senarai) <= MAX_JAWAPAN_DITERIMA):
        raise ValueError(
            f"jawapan_diterima mesti mengandungi 1 hingga {MAX_JAWAPAN_DITERIMA} item."
        )
    for jawapan in senarai:
        if not isinstance(jawapan, str) or not jawapan.strip():
            raise ValueError("Setiap jawapan dalam jawapan_diterima tidak boleh kosong.")


def _sahkan_betul_salah(
    pilihan: dict[str, str] | None,
    jawapan_betul: dict[str, Any],
) -> None:
    if pilihan is not None:
        raise ValueError("pilihan mesti null untuk soalan betul/salah.")
    if set(jawapan_betul.keys()) != {"nilai"}:
        raise ValueError("jawapan_betul mesti berbentuk {\"nilai\": true} atau {\"nilai\": false}.")
    if not isinstance(jawapan_betul.get("nilai"), bool):
        raise ValueError("jawapan_betul.nilai mesti boolean.")


def _sahkan_padanan(
    pilihan: dict[str, str] | None,
    jawapan_betul: dict[str, Any],
) -> None:
    if pilihan is not None:
        raise ValueError("pilihan mesti null untuk soalan padanan.")
    if set(jawapan_betul.keys()) != {"pasangan"}:
        raise ValueError("jawapan_betul mesti berbentuk {\"pasangan\": [...]}.")
    pasangan = jawapan_betul.get("pasangan")
    if not isinstance(pasangan, list):
        raise ValueError("pasangan mesti senarai pasangan kiri-kanan.")
    if not (MIN_PASANGAN <= len(pasangan) <= MAX_PASANGAN):
        raise ValueError(
            f"pasangan mesti mengandungi {MIN_PASANGAN} hingga {MAX_PASANGAN} item."
        )
    kiri_set: set[str] = set()
    kanan_set: set[str] = set()
    for item in pasangan:
        if not isinstance(item, dict):
            raise ValueError("Setiap pasangan mesti objek dengan kiri dan kanan.")
        kiri = item.get("kiri")
        kanan = item.get("kanan")
        if not isinstance(kiri, str) or not kiri.strip():
            raise ValueError("Setiap pasangan mesti mempunyai kiri yang tidak kosong.")
        if not isinstance(kanan, str) or not kanan.strip():
            raise ValueError("Setiap pasangan mesti mempunyai kanan yang tidak kosong.")
        if kiri in kiri_set:
            raise ValueError("Nilai kiri mesti unik dalam pasangan.")
        if kanan in kanan_set:
            raise ValueError("Nilai kanan mesti unik dalam pasangan.")
        kiri_set.add(kiri)
        kanan_set.add(kanan)