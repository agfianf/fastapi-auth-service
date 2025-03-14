import datetime as dt

from datetime import datetime

from pydantic import BaseModel, Field


class BaseAudit(BaseModel):
    created_at: datetime | None = None
    created_by: str | None = None
    updated_at: datetime | None = None
    updated_by: str | None = None
    deleted_at: datetime | None = None
    deleted_by: str | None = None


class BaseAuditCreatedBy(BaseModel):
    created_by: str | None = Field(
        default=None,
        description="The user who created the record",
    )


class BaseAuditUpdatedBy(BaseModel):
    updated_by: str | None = Field(
        default=None,
        description="The user who updated the record",
    )


class BaseAuditDeletedBy(BaseModel):
    deleted_by: str | None = Field(
        default=None,
        description="The user who deleted the record",
    )

    def get_deleted_at_utc(self) -> datetime:
        return datetime.now(dt.UTC)


class BaseAuditActive(BaseModel):
    created_at: datetime | None = None
    created_by: str | None = None
    updated_at: datetime | None = None
    updated_by: str | None = None
