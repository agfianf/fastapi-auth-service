from sqlalchemy import (
    VARCHAR,
    Column,
    ForeignKey,
    Integer,
    Table,
    UniqueConstraint,
)
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
    Column("is_active", VARCHAR(225), nullable=False, server_default="false"),
    *default_base_audit,
)

user_services_table = Table(
    "user_services",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_uuid", UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False),
    Column("service_uuid", UUID(as_uuid=True), ForeignKey("services.uuid"), nullable=False),
    *default_base_audit_junction,

    UniqueConstraint(
        "user_uuid",
        "service_uuid",
        name="uq_user_service",
    ),
)

# fmt: on
