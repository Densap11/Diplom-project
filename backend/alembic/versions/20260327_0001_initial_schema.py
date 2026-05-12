"""initial schema

Revision ID: 20260327_0001
Revises:
Create Date: 2026-03-27 01:20:00
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "20260327_0001"
down_revision = None
branch_labels = None
depends_on = None


user_role_enum = sa.Enum("student", "organizer", "admin", name="userrole")
event_status_enum = sa.Enum("draft", "published", "archived", name="eventstatus")
event_format_enum = sa.Enum("offline", "online", "mixed", name="eventformat")
registration_status_enum = sa.Enum(
    "confirmed",
    "cancelled",
    "waiting_list",
    name="registrationstatus",
)
user_role_column_enum = postgresql.ENUM(
    "student", "organizer", "admin", name="userrole", create_type=False
)
event_status_column_enum = postgresql.ENUM(
    "draft", "published", "archived", name="eventstatus", create_type=False
)
event_format_column_enum = postgresql.ENUM(
    "offline", "online", "mixed", name="eventformat", create_type=False
)
registration_status_column_enum = postgresql.ENUM(
    "confirmed",
    "cancelled",
    "waiting_list",
    name="registrationstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    user_role_enum.create(bind, checkfirst=True)
    event_status_enum.create(bind, checkfirst=True)
    event_format_enum.create(bind, checkfirst=True)
    registration_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
    )
    op.create_index("ix_categories_id", "categories", ["id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("faculty", sa.String(length=255), nullable=True),
        sa.Column("study_group", sa.String(length=100), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("role", user_role_column_enum, nullable=False, server_default="student"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id", "users", ["id"], unique=False)

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("short_description", sa.String(length=500), nullable=False),
        sa.Column("full_description", sa.Text(), nullable=False),
        sa.Column("event_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("contacts", sa.String(length=255), nullable=False),
        sa.Column("max_participants", sa.Integer(), nullable=True),
        sa.Column("is_unlimited", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", event_status_column_enum, nullable=False, server_default="draft"),
        sa.Column("format", event_format_column_enum, nullable=False, server_default="offline"),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("organizer_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["organizer_id"], ["users.id"]),
    )
    op.create_index("ix_events_id", "events", ["id"], unique=False)

    op.create_table(
        "event_registrations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            registration_status_column_enum,
            nullable=False,
            server_default="confirmed",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.UniqueConstraint("student_id", "event_id", name="uq_student_event_registration"),
    )
    op.create_index("ix_event_registrations_id", "event_registrations", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_event_registrations_id", table_name="event_registrations")
    op.drop_table("event_registrations")

    op.drop_index("ix_events_id", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_users_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_categories_id", table_name="categories")
    op.drop_table("categories")

    bind = op.get_bind()
    registration_status_enum.drop(bind, checkfirst=True)
    event_format_enum.drop(bind, checkfirst=True)
    event_status_enum.drop(bind, checkfirst=True)
    user_role_enum.drop(bind, checkfirst=True)
