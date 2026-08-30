from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["super_admin", "admin", "murid"]

PASSWORD_MIN = 8
PASSWORD_MAX = 128
MAX_BULK_ITEMS = 500


class CreateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nama_first: str = Field(min_length=1, max_length=50)
    nama_last: str = Field(min_length=1, max_length=50)
    username: str = Field(min_length=1, max_length=50)
    role: Role
    kata_laluan_awal: str = Field(min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)
    kelas_id: int | None = Field(default=None, gt=0)


class UpdateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nama_first: str | None = Field(default=None, min_length=1, max_length=50)
    nama_last: str | None = Field(default=None, min_length=1, max_length=50)
    aktif: bool | None = None
    kelas_id: int | None = Field(default=None, gt=0)


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kata_laluan_baru: str = Field(min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)


class BulkUserIdsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ids: list[Annotated[int, Field(gt=0)]] = Field(min_length=1, max_length=MAX_BULK_ITEMS)


class BulkUserDeactivateSummary(BaseModel):
    mesej: str
    dinyahaktifkan: int


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nama_first: str
    nama_last: str
    role: str
    aktif: bool
    mesti_tukar_kata_laluan: bool
    kelas_id: int | None
    created_at: datetime


class GuruDirectoryResponse(BaseModel):
    id: int
    nama_first: str
    nama_last: str


class UserFilterParams(BaseModel):
    role: Role | None = None
    carian: str | None = None
    page: int | None = None
    page_size: int | None = None
