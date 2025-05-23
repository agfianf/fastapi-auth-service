from sqlalchemy import VARCHAR, Boolean, Column, ForeignKey, Integer, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.helpers.database import metadata
from app.models._base_default import generate_base_audit


default_base_audit = generate_base_audit()
default_base_audit_junction = generate_base_audit()

# fmt: off
services_table = Table(
    "services",
    metadata,
    Column("uuid", UUID(as_uuid=True), primary_key=True),
    Column("name", VARCHAR(225), nullable=False, unique=True),
    Column("location", VARCHAR(255), nullable=True),
    Column("description", VARCHAR(255), nullable=True),
    Column("is_active", Boolean, nullable=False, server_default="false"),
    *default_base_audit,
)

service_memberships_table = Table(
    "service_memberships",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_uuid", UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False),
    Column("service_uuid", UUID(as_uuid=True), ForeignKey("services.uuid"), nullable=False),
    Column("business_role_id", Integer, ForeignKey("business_roles.id"), nullable=True),
    Column("is_active", Boolean, nullable=False, server_default="false"),
    *default_base_audit_junction,

    UniqueConstraint(
        "user_uuid",
        "service_uuid",
        "business_role_id",
        name="uq_service_memberships_user_service_role",
    ),
)

# fmt: on
