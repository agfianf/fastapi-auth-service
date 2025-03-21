from pydantic import BaseModel, Field

from app.schemas.users import UserMembershipQueryReponse


class MemberDetailsResponse(UserMembershipQueryReponse):
    """Member details response schema."""

    pass


class UpdateMemberResponse(BaseModel):
    """Base response for member update operations."""

    access_token: str = Field(
        ...,
        description="New JWT access token after update",
        examples=["eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."],
    )
    user: UserMembershipQueryReponse = Field(
        ...,
        description="Updated user details",
    )


class UpdateMemberMFAResponse(UpdateMemberResponse):
    """Response for MFA update operations."""

    qr_code_bs64: str | None = Field(
        ...,
        description="Base64 encoded QR code image for MFA setup",
    )


class MFAQRCodeResponse(BaseModel):
    """Response for MFA QR code request."""

    qr_code_bs64: str = Field(
        ...,
        description="Base64 encoded QR code image for MFA setup",
    )
