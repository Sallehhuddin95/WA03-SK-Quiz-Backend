"""seed data rujukan: subjects, tahun, topics

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-23
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "INSERT INTO subjects (id, nama) VALUES (1, 'Matematik')"
    )
    op.execute(
        "INSERT INTO tahun (id, subject_id, nama) VALUES (1, 1, 'Tahun 6')"
    )
    op.execute(
        "INSERT INTO topics (id, tahun_id, nama) VALUES "
        "(1, 1, 'Nombor dan Operasi'), "
        "(2, 1, 'Ukuran dan Geometri'), "
        "(3, 1, 'Pengurusan Data')"
    )


def downgrade() -> None:
    op.execute("DELETE FROM topics")
    op.execute("DELETE FROM tahun")
    op.execute("DELETE FROM subjects")