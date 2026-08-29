from pydantic import BaseModel, ConfigDict, Field

from app.schemas.kelas import KelasBrief
from app.schemas.user import PASSWORD_MAX, PASSWORD_MIN


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=50)
    kata_laluan: str = Field(min_length=1)


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kata_laluan_semasa: str = Field(min_length=1)
    kata_laluan_baru: str = Field(min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)


class SessionUserResponse(BaseModel):
    id: int
    username: str
    nama_first: str
    nama_last: str
    role: str
    mesti_tukar_kata_laluan: bool
    kelas: KelasBrief | None


LoginResponse = SessionUserResponse
MeResponse = SessionUserResponse
