"""milestone_2_1_auth_and_schools

Revision ID: b0ab4e9460bd
Revises: 638214c31b7d
Create Date: 2026-06-29

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b0ab4e9460bd"
down_revision: Union[str, Sequence[str], None] = "638214c31b7d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add schools, teachers, teacher_schools tables and school_id to classrooms."""
    op.create_table(
        "schools",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "teachers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=60), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "teacher_schools",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending_admin", "pending_school", "approved", "rejected", name="teacher_school_status"),
            nullable=False,
        ),
        sa.Column("resolved_by", sa.Integer(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("requested_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["resolved_by"], ["teachers.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("teacher_id", "school_id", name="uq_teacher_school"),
    )
    with op.batch_alter_table("classrooms") as batch_op:
        batch_op.add_column(sa.Column("school_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_classrooms_school_id_schools", "schools", ["school_id"], ["id"])


def downgrade() -> None:
    """Remove schools, teachers, teacher_schools and school_id from classrooms."""
    with op.batch_alter_table("classrooms") as batch_op:
        batch_op.drop_constraint("fk_classrooms_school_id_schools", type_="foreignkey")
        batch_op.drop_column("school_id")
    op.drop_table("teacher_schools")
    op.drop_table("teachers")
    op.drop_table("schools")
    op.execute("DROP TYPE IF EXISTS teacher_school_status")
