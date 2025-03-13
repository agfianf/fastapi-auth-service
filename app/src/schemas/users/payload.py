from pydantic import BaseModel, EmailStr, Field
from src.helpers.generator import generate_uuid


class CreateUser(BaseModel):
    email: EmailStr = Field(..., description="Email of the user")
    username: str = Field(..., description="Username of the user")
    password: str = Field(..., description="Password of the user")
    password_confirm: str = Field(..., description="Password confirmation of the user")

    firstname: str = Field(..., description="Firstname of the user")
    midname: str | None = Field(None, description="Midname of the user")
    lastname: str | None = Field(None, description="Lastname of the user")

    role_id: int | None = Field(None, description="ID of the role")
    phone: str | None = Field(None, description="Phone of the user")
    telegram: str | None = Field(None, description="Telegram of the user")

    def transform(self) -> dict:
        uuid = generate_uuid()
        data = self.model_dump
        data["uuid"] = uuid
        data["password_hash"] = self.password
        return data


class UpdateUser(BaseModel):
    uuid: str = Field(..., description="UUID of the user")
    role_id: int | None = Field(None, description="ID of the role")
    username: str | None = Field(None, description="Username of the user")
    firstname: str | None = Field(None, description="Firstname of the user")
    midname: str | None = Field(None, description="Midname of the user")
    lastname: str | None = Field(None, description="Lastname of the user")
    email: EmailStr | None = Field(None, description="Email of the user")
    phone: str | None = Field(None, description="Phone of the user")
    telegram: str | None = Field(None, description="Telegram of the user")
    is_active: bool | None = Field(None, description="Is the user active")

    def transform(self) -> dict:
        return self.model_dump(exclude_none=True)


class UpdatePasswordUserOnly(BaseModel):
    uuid: str = Field(..., description="UUID of the user")
    password: str = Field(..., description="Password of the user")
    password_confirm: str = Field(..., description="Password confirmation of the user")

    def transform(self) -> dict:
        return self.model_dump()
