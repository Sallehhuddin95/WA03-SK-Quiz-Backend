from pydantic import BaseModel, ConfigDict


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nama: str


class TahunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    nama: str