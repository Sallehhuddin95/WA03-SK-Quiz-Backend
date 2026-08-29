from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class GuruKelas(Base):
    """Jadual pemilikan kelas: guru yang mengajar kelas mana (skop own)."""

    __tablename__ = "guru_kelas"

    guru_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    kelas_id: Mapped[int] = mapped_column(
        ForeignKey("kelas.id", ondelete="CASCADE"), primary_key=True
    )


class KelasShare(Base):
    """Jadual perkongsian kelas: pemberian akses baca sahaja kepada guru lain."""

    __tablename__ = "kelas_share"

    kelas_id: Mapped[int] = mapped_column(
        ForeignKey("kelas.id", ondelete="CASCADE"), primary_key=True
    )
    shared_with_guru_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
