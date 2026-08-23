from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    tahun_id: Mapped[int] = mapped_column(
        ForeignKey("tahun.id", ondelete="CASCADE"), nullable=False
    )
    nama: Mapped[str] = mapped_column(String(100), nullable=False)