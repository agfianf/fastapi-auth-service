from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field, SecretStr, model_validator


class UpdatePasswordPayload(BaseModel):
    current_password: SecretStr = Field(
        ...,
        min_length=8,
        max_length=255,
        description="Current password of the user",
    )
    new_password: SecretStr = Field(
        ...,
        min_length=8,
        max_length=255,
        description="New password of the user",
    )
    new_password_confirm: SecretStr = Field(
        ...,
        min_length=8,
        max_length=255,
        description="Confirmation of the new password",
    )


class UpdateMFAPayload(BaseModel):
    mfa_enabled: bool = Field(
        ...,
        description="Enable or disable MFA",
        examples=[True, False],
    )
    mfa_code: str | None = Field(
        None,
        min_length=6,
        max_length=6,
        description="MFA code for verification when disabling MFA",
        examples=["123456"],
    )

    @model_validator(mode="before")
    @classmethod
    def preprocess_input_data(cls, data: dict) -> dict:
        """Preprocess input data to handle empty strings."""
        for key in data:
            if data[key] == "":
                data[key] = None

        if data["mfa_code"] is not None and len(data["mfa_code"]) != 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA code must be exactly 6 digits",
            )

        return data


class UpdateMemberPayload(BaseModel):
    email: EmailStr | None = Field(
        None,
        min_length=5,
        max_length=255,
        description="Email of the user",
        examples=["johndoe@email.com"],
    )
    username: str | None = Field(
        None,
        min_length=5,
        max_length=255,
        description="Username of the user",
        examples=["johndoe"],
    )
    firstname: str | None = Field(
        None,
        description="Firstname of the user",
        examples=["John"],
    )
    midname: str | None = Field(
        None,
        description="Midname of the user",
        examples=[None],
    )
    lastname: str | None = Field(
        None,
        description="Lastname of the user",
        examples=[None],
    )
    phone: str | None = Field(
        None,
        description="Phone of the user",
        examples=[None],
    )
    telegram: str | None = Field(
        None,
        description="Telegram of the user",
        examples=[None],
    )

    @model_validator(mode="before")
    @classmethod
    def preprocess_input_data(cls, data: dict) -> dict:
        """Preprocess input data to handle empty strings."""
        for key in data:
            if data[key] == "":
                data[key] = None

        if "username" in data and data["username"] and " " in data["username"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username cannot contain space",
            )

        return data

    def transform(self) -> dict:
        """Transform payload to dictionary for update operation."""
        return self.model_dump(exclude_none=True)
