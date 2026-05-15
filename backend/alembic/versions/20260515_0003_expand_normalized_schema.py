"""expand normalized schema

Revision ID: 20260515_0003
Revises: 20260327_0002
Create Date: 2026-05-15 12:00:00
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "20260515_0003"
down_revision = "20260327_0002"
branch_labels = None
depends_on = None


roles_table = sa.table(
    "roles",
    sa.column("name", sa.String),
    sa.column("title", sa.String),
    sa.column("description", sa.String),
)
permissions_table = sa.table(
    "permissions",
    sa.column("code", sa.String),
    sa.column("description", sa.String),
)


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_roles_id", "roles", ["id"], unique=False)
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"], unique=True)
    op.create_index("ix_permissions_id", "permissions", ["id"], unique=False)

    op.bulk_insert(
        roles_table,
        [
            {"name": "student", "title": "Студент", "description": "Участник мероприятий"},
            {"name": "organizer", "title": "Организатор", "description": "Создает и ведет мероприятия"},
            {"name": "admin", "title": "Администратор", "description": "Управляет системой"},
        ],
    )
    op.bulk_insert(
        permissions_table,
        [
            {"code": "events:read", "description": "Просмотр опубликованных мероприятий"},
            {"code": "events:create", "description": "Создание мероприятий"},
            {"code": "events:manage-own", "description": "Управление своими мероприятиями"},
            {"code": "events:manage-all", "description": "Управление всеми мероприятиями"},
            {"code": "registrations:create", "description": "Запись на мероприятия"},
            {"code": "users:manage", "description": "Управление пользователями и ролями"},
            {"code": "categories:manage", "description": "Управление категориями"},
            {"code": "comments:create", "description": "Создание комментариев"},
        ],
    )

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"]),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )
    op.create_index("ix_role_permissions_id", "role_permissions", ["id"], unique=False)
    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r
        JOIN permissions p ON
          (r.name = 'student' AND p.code IN ('events:read', 'registrations:create', 'comments:create'))
          OR (r.name = 'organizer' AND p.code IN ('events:read', 'events:create', 'events:manage-own', 'comments:create'))
          OR (r.name = 'admin')
        """
    )

    op.add_column("users", sa.Column("role_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_users_role_id_roles", "users", "roles", ["role_id"], ["id"])
    op.execute(
        """
        UPDATE users
        SET role_id = roles.id
        FROM roles
        WHERE roles.name = users.role::text
        """
    )
    op.alter_column("users", "role_id", nullable=False)

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("faculty", sa.String(length=255), nullable=True),
        sa.Column("study_group", sa.String(length=100), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_profiles_id", "user_profiles", ["id"], unique=False)
    op.execute(
        """
        INSERT INTO user_profiles (user_id, faculty, study_group, phone)
        SELECT id, faculty, study_group, phone
        FROM users
        """
    )

    op.drop_column("users", "role")
    op.drop_column("users", "faculty")
    op.drop_column("users", "study_group")
    op.drop_column("users", "phone")

    op.create_table(
        "event_tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_event_tags_id", "event_tags", ["id"], unique=False)
    op.create_index("ix_event_tags_name", "event_tags", ["name"], unique=True)

    op.create_table(
        "event_tag_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["event_tags.id"]),
        sa.UniqueConstraint("event_id", "tag_id", name="uq_event_tag_link"),
    )
    op.create_index("ix_event_tag_links_id", "event_tag_links", ["id"], unique=False)

    op.create_table(
        "event_comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
    )
    op.create_index("ix_event_comments_id", "event_comments", ["id"], unique=False)

    bind = op.get_bind()
    postgresql.ENUM(name="userrole").drop(bind, checkfirst=True)


def downgrade() -> None:
    user_role_enum = postgresql.ENUM("student", "organizer", "admin", name="userrole")
    bind = op.get_bind()
    user_role_enum.create(bind, checkfirst=True)

    op.add_column("users", sa.Column("phone", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("study_group", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("faculty", sa.String(length=255), nullable=True))
    op.add_column(
        "users",
        sa.Column("role", postgresql.ENUM(name="userrole", create_type=False), nullable=True),
    )
    op.execute(
        """
        UPDATE users
        SET role = roles.name::userrole
        FROM roles
        WHERE roles.id = users.role_id
        """
    )
    op.execute(
        """
        UPDATE users
        SET
          faculty = user_profiles.faculty,
          study_group = user_profiles.study_group,
          phone = user_profiles.phone
        FROM user_profiles
        WHERE user_profiles.user_id = users.id
        """
    )
    op.alter_column("users", "role", nullable=False)

    op.drop_index("ix_event_comments_id", table_name="event_comments")
    op.drop_table("event_comments")

    op.drop_index("ix_event_tag_links_id", table_name="event_tag_links")
    op.drop_table("event_tag_links")

    op.drop_index("ix_event_tags_name", table_name="event_tags")
    op.drop_index("ix_event_tags_id", table_name="event_tags")
    op.drop_table("event_tags")

    op.drop_index("ix_user_profiles_id", table_name="user_profiles")
    op.drop_table("user_profiles")

    op.drop_constraint("fk_users_role_id_roles", "users", type_="foreignkey")
    op.drop_column("users", "role_id")

    op.drop_index("ix_role_permissions_id", table_name="role_permissions")
    op.drop_table("role_permissions")

    op.drop_index("ix_permissions_id", table_name="permissions")
    op.drop_index("ix_permissions_code", table_name="permissions")
    op.drop_table("permissions")

    op.drop_index("ix_roles_name", table_name="roles")
    op.drop_index("ix_roles_id", table_name="roles")
    op.drop_table("roles")
