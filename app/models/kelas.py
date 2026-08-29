from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Kelas(Base):
    __tablename__ = "kelas"
    __table_args__ = (
        CheckConstraint("darjah BETWEEN 1 AND 6", name="chk_kelas_darjah"),
        UniqueConstraint("darjah", "nama", name="uq_kelas_darjah_nama"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nama: Mapped[str] = mapped_column(String(50), nullable=False)
    darjah: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    murids: Mapped[list["User"]] = relationship(back_populates="kelas")
