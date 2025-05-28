from typing import Self

from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field, SecretStr, model_validator

from app.helpers.auth import get_password_hash
from app.helpers.generator import generate_uuid
from app.helpers.password_validator import PasswordValidate


class CreateUserPayload(BaseModel):
    email: EmailStr = Field(
        ...,
        min_length=5,
        max_length=255,
        description="Email of the user",
        examples=["johndoe@email.com"],
    )
    username: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="Username of the user",
        examples=["johndoe"],
    )
    password: SecretStr = Field(
        ...,
        min_length=8,
        max_length=255,
        description="Password of the user",
    )
    password_confirm: SecretStr = Field(
        ...,
        min_length=8,
        max_length=255,
        description="Password confirmation of the user",
    )

    firstname: str = Field(..., description="Firstname of the user", examples=["John"])
    midname: str | None = Field(None, description="Midname of the user", examples=[None])
    lastname: str | None = Field(None, description="Lastname of the user", examples=[None])

    role_id: int | None = Field(None, description="ID of the role", examples=[None])
    phone: str | None = Field(None, description="Phone of the user", examples=[None])
    telegram: str | None = Field(None, description="Telegram of the user", examples=[None])
    mfa_enabled: bool = Field(False, description="Is MFA enabled", examples=[False])

    @model_validator(mode="before")
    @classmethod
    def preproces_input_data(cls, data: dict) -> dict:  # noqa:ANN102
        for key in data:
            if data[key] == "":
                data[key] = None

        if " " in data["username"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username cannot contain space",
            )
        return data

    @model_validator(mode="after")
    def validate_password(self) -> Self:  # noqa:ANN102
        is_valid, msgs = PasswordValidate.validate_password(
            username=self.username,
            pwd=self.password.get_secret_value(),
            conf_pwd=self.password_confirm.get_secret_value(),
        )

        if is_valid:
            return self
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(msgs),
        )

    def transform(self) -> dict:
        data = self.model_dump(exclude={"password_confirm", "password"}, exclude_none=True)

        # generate uuid for user unique identifier
        data["uuid"] = generate_uuid()

        # generate password hash for user security before storing it
        hashed_password = get_password_hash(self.password.get_secret_value())
        data["password_hash"] = hashed_password

        # created_by is the user who created the account
        data["created_by"] = data["email"]
        data["is_active"] = False

        return data


class ResetPasswordPayload(BaseModel):
    reset_token: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Reset password token",
        examples=["reset_token_example"],
    )
    password: SecretStr = Field(
        ...,
        min_length=8,
        max_length=255,
        description="Password of the user",
    )
    password_confirm: SecretStr = Field(
        ...,
        min_length=8,
        max_length=255,
        description="Password confirmation of the user",
    )

    def validate_password(self, username) -> Self:  # noqa:ANN102
        is_valid, msgs = PasswordValidate.validate_password(
            username=username,
            pwd=self.password.get_secret_value(),
            conf_pwd=self.password_confirm.get_secret_value(),
        )

        if is_valid:
            return self
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(msgs),
        )


class SignInPayload(BaseModel):
    username: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="Username of the user",
        examples=["johndoe"],
    )
    password: SecretStr = Field(
        ...,
        min_length=8,
        max_length=255,
        description="Password of the user",
    )
