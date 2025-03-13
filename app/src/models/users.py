from sqlalchemy import VARCHAR, Boolean, Column, Integer, String, Table, text
from src.helpers.database import metadata
from src.models._base_default import generate_base_audit


default_base_audit = generate_base_audit()

users_table = Table(
    "users",
    metadata,
    Column("uuid", VARCHAR(36), primary_key=True),
    Column("role_id", Integer, nullable=True),
    Column("username", VARCHAR(225), nullable=False, unique=True),
    Column("firstname", VARCHAR(225), nullable=False),
    Column("midname", VARCHAR(225), nullable=True),
    Column("lastname", VARCHAR(225), nullable=True),
    Column("email", VARCHAR(225), nullable=False, unique=True),
    Column("phone", VARCHAR(225), nullable=True, unique=True),
    Column("telegram", VARCHAR(225), nullable=True, unique=True),
    Column("password_hash", VARCHAR(225), nullable=False),
    Column("is_active", VARCHAR(225), nullable=False, server_default=text("false")),
    Column("mfa_enabled", Boolean(), nullable=True, server_default=text("false")),  # noqa: E501
    Column("mfa_secret", String(255), nullable=True),
    *default_base_audit,
)
