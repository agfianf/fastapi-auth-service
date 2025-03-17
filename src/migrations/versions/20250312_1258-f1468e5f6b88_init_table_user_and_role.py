"""init table user and role.

Revision ID: f1468e5f6b88
Revises:
Create Date: 2025-03-12 12:58:06.147780

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f1468e5f6b88"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def generate_base_audit() -> list:
    """Generate base audit columns."""
    return [
        sa.Column(
            "created_at",
            type_=sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            type_=sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
        ),
        sa.Column(
            "deleted_at",
            type_=sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.Column("deleted_by", sa.String(), nullable=True),
    ]


def upgrade() -> None:
    """Upgrade schema."""
    # Create roles table first
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.VARCHAR(225), nullable=False, unique=True),
        sa.Column("description", sa.String(), nullable=True),
        *generate_base_audit(),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_roles_name", "name"),
    )

    op.create_table(
        "users",
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(255), nullable=False, unique=True),
        sa.Column("firstname", sa.String(255), nullable=False),
        sa.Column("midname", sa.String(255), nullable=True),
        sa.Column("lastname", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(20), nullable=True, unique=True),
        sa.Column("telegram", sa.String(), nullable=True, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("mfa_secret", sa.String(255), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        *generate_base_audit(),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name="fk_user_role_id",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        sa.PrimaryKeyConstraint("uuid"),
        sa.Index("ix_user_email", "email"),
        sa.Index("ix_user_username", "username"),
    )

    op.create_table(
        "services",
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        *generate_base_audit(),
        sa.PrimaryKeyConstraint("uuid"),
        sa.Index("ix_service_name", "name"),
    )

    # Create a junction table to establish many-to-many relationship between
    # users and services
    op.create_table(
        "service_memberships",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user_uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("service_uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        *generate_base_audit(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_uuid"],
            ["users.uuid"],
            name="fk_service_memberships_user_uuid",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name="fk_service_memberships_role_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["service_uuid"],
            ["services.uuid"],
            name="fk_service_memberships_service_uuid",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "user_uuid",
            "service_uuid",
            "role_id",
            name="uq_service_memberships_user_service_role",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("service_memberships")
    op.drop_table("services")
    op.drop_table("users")
    op.drop_table("roles")
