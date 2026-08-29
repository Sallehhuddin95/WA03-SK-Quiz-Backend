from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KelasBrief(BaseModel):
    id: int
    nama: str
    darjah: int


class GuruBrief(BaseModel):
    id: int
    nama_first: str
    nama_last: str


class CreateKelasRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nama: str = Field(min_length=1, max_length=50)
    darjah: int = Field(ge=1, le=6)


class UpdateKelasRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nama: str | None = Field(default=None, min_length=1, max_length=50)
    darjah: int | None = Field(default=None, ge=1, le=6)


class ShareKelasRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    guru_ids: list[int] = Field(default_factory=list)


class KelasResponse(BaseModel):
    id: int
    nama: str
    darjah: int
    guru_owners: list[GuruBrief]
    shared_with: list[GuruBrief]
    created_at: datetime
