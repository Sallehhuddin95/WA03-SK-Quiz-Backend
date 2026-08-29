"""auth dan rbac: users, sessions, kelas, guru_kelas, kelas_share

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-25
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "kelas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nama", sa.String(length=50), nullable=False),
        sa.Column("darjah", sa.Integer(), nullable=False),
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
        "chk_kelas_darjah", "kelas", "darjah BETWEEN 1 AND 6"
    )
    op.create_unique_constraint(
        "uq_kelas_darjah_nama", "kelas", ["darjah", "nama"]
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("nama_first", sa.String(length=50), nullable=False),
        sa.Column("nama_last", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column(
            "aktif",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "mesti_tukar_kata_laluan",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "kelas_id",
            sa.Integer(),
            sa.ForeignKey("kelas.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
    op.create_unique_constraint("uq_users_username", "users", ["username"])
    op.create_check_constraint(
        "chk_users_role",
        "users",
        "role IN ('super_admin', 'admin', 'murid')",
    )
    op.create_index("ix_users_kelas_id", "users", ["kelas_id"])

    op.create_table(
        "guru_kelas",
        sa.Column(
            "guru_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "kelas_id",
            sa.Integer(),
            sa.ForeignKey("kelas.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "kelas_share",
        sa.Column(
            "kelas_id",
            sa.Integer(),
            sa.ForeignKey("kelas.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "shared_with_guru_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_unique_constraint("uq_sessions_token_hash", "sessions", ["token_hash"])
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])

    op.add_column(
        "quiz_attempts",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_quiz_attempts_user_id", "quiz_attempts", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_quiz_attempts_user_id", table_name="quiz_attempts")
    op.drop_column("quiz_attempts", "user_id")

    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")
    op.drop_table("kelas_share")
    op.drop_table("guru_kelas")
    op.drop_index("ix_users_kelas_id", table_name="users")
    op.drop_table("users")
    op.drop_table("kelas")