from pydantic import Field

from app.schemas.users.base import UserBase
from app.schemas.users.payload import CreateUserPayload


class CreateUserQuery(CreateUserPayload):
    # transform() already implemented in PayloadUCreateUser2FA

    mfa_secret: str | None = Field(
        None,
        description="MFA secret for the account",
        examples=["JBSWY3DPEHPK3PXP"],
    )


class CreateUserQueryResponse(UserBase):
    password_hash: str | None = Field(None, exclude=True)
    mfa_secret: str | None = Field(None, exclude=True)
