from sqlalchemy import (
    TIMESTAMP,
    Column,
    String,
    func,
)


def generate_base_audit() -> list:
    return [
        Column(
            "created_at",
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
        Column(
            "updated_at",
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
        Column("deleted_at", TIMESTAMP(timezone=True), nullable=True),
        Column("created_by", String(225), nullable=True),
        Column("updated_by", String(225), nullable=True),
        Column("deleted_by", String(225), nullable=True),
    ]
