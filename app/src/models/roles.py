from sqlalchemy import VARCHAR, Column, Integer, Table, Text
from src.helpers.database import metadata
from src.models._base_default import generate_base_audit


default_base_audit = generate_base_audit()


# fmt: off
roles_table = Table(
    "roles",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", VARCHAR(225), nullable=False, unique=True),
    Column("description", Text(), nullable=True),
    *default_base_audit,
)
# fmt: on
