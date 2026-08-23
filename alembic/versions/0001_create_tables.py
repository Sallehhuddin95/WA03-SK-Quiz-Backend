"""cipta jadual asas skema sk_quiz

Revision ID: 0001
Revises:
Create Date: 2026-08-23
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nama", sa.String(length=100), nullable=False),
    )

    op.create_table(
        "tahun",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "subject_id",
            sa.Integer(),
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nama", sa.String(length=50), nullable=False),
    )
    op.create_index("idx_tahun_subject_id", "tahun", ["subject_id"])

    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "tahun_id",
            sa.Integer(),
            sa.ForeignKey("tahun.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nama", sa.String(length=100), nullable=False),
    )
    op.create_index("idx_topics_tahun_id", "topics", ["tahun_id"])

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "topic_id",
            sa.Integer(),
            sa.ForeignKey("topics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("jenis_soalan", sa.String(length=30), nullable=False),
        sa.Column("tahap_kesukaran", sa.String(length=15), nullable=False),
        sa.Column(
            "status", sa.String(length=15), nullable=False, server_default="aktif"
        ),
        sa.Column("teks_soalan", sa.Text(), nullable=False),
        sa.Column("pilihan", postgresql.JSONB(), nullable=True),
        sa.Column("jawapan_betul", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_check_constraint(
        "chk_jenis_soalan",
        "questions",
        "jenis_soalan IN ('aneka_pilihan', 'isi_tempat_kosong', 'betul_salah', 'padanan')",
    )
    op.create_check_constraint(
        "chk_tahap_kesukaran",
        "questions",
        "tahap_kesukaran IN ('mudah', 'sederhana', 'sukar')",
    )
    op.create_check_constraint(
        "chk_status",
        "questions",
        "status IN ('aktif', 'tidak_aktif')",
    )
    op.create_index("idx_questions_topic_id", "questions", ["topic_id"])
    op.create_index("idx_questions_status", "questions", ["status"])
    op.create_index(
        "idx_questions_pemilihan",
        "questions",
        ["topic_id", "tahap_kesukaran", "jenis_soalan", "status"],
    )

    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "topic_id",
            sa.Integer(),
            sa.ForeignKey("topics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tahap_kesukaran", sa.String(length=15), nullable=False),
        sa.Column("nama_peserta", sa.String(length=50), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="dalam_progres",
        ),
        sa.Column("skor", sa.Integer(), nullable=True),
        sa.Column(
            "jumlah_soalan", sa.Integer(), nullable=False, server_default="10"
        ),
        sa.Column(
            "masa_mula",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("masa_hantar", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_check_constraint(
        "chk_attempt_tahap",
        "quiz_attempts",
        "tahap_kesukaran IN ('mudah', 'sederhana', 'sukar')",
    )
    op.create_check_constraint(
        "chk_attempt_status",
        "quiz_attempts",
        "status IN ('dalam_progres', 'selesai')",
    )
    op.create_check_constraint(
        "chk_nama_peserta",
        "quiz_attempts",
        "char_length(trim(nama_peserta)) BETWEEN 1 AND 50",
    )
    op.create_index("idx_attempts_topic_id", "quiz_attempts", ["topic_id"])
    op.create_index("idx_attempts_participant", "quiz_attempts", ["nama_peserta"])
    op.create_index("idx_attempts_status", "quiz_attempts", ["status"])
    op.create_index(
        "idx_attempts_created", "quiz_attempts", [sa.text("created_at DESC")]
    )

    op.create_table(
        "quiz_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "quiz_attempt_id",
            sa.Integer(),
            sa.ForeignKey("quiz_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey("questions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("data_jawapan", postgresql.JSONB(), nullable=True),
        sa.Column("adalah_betul", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_answers_attempt_id", "quiz_answers", ["quiz_attempt_id"])
    op.create_index("idx_answers_question_id", "quiz_answers", ["question_id"])


def downgrade() -> None:
    op.drop_table("quiz_answers")
    op.drop_table("quiz_attempts")
    op.drop_table("questions")
    op.drop_table("topics")
    op.drop_table("tahun")
    op.drop_table("subjects")