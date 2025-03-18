from pydantic import BaseModel, Field

from app.schemas.users.query import CreateUserQueryResponse


class CreateUserResponse(BaseModel):
    qr_code_bs64: str | None = None
    user: CreateUserQueryResponse


class SignInResponse(BaseModel):
    access_token: str | None = Field(
        None,
        description="JWT access token for authentication",
        examples=["eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"],
    )
    mfa_token: str | None = Field(
        None,
        description="JWT MFA token for authentication",
        examples=["eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"],
    )
    mfa_required: bool = Field(False, description="MFA required for login")


class VerifyMFAResponse(BaseModel):
    access_token: str | None = Field(
        None,
        description="JWT access token for authentication",
        examples=["eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"],
    )
