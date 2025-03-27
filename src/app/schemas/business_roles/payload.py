from pydantic import BaseModel, Field


class BusinessRolePayloadBase(BaseModel):
    name: str = Field(..., description="Name of the business role", min_length=1, max_length=100)
    description: str | None = Field(None, description="Description of the business role")

    def transform(self) -> dict:
        """Transform to database format."""
        result = self.model_dump(exclude_unset=True)
        return result


class CreateBusinessRole(BusinessRolePayloadBase):
    """Create business role payload."""

    pass


class UpdateBusinessRole(BusinessRolePayloadBase):
    """Update business role payload."""

    name: str | None = Field(None, description="Name of the business role")
