from pydantic import BaseModel


class CreateUserResponse(BaseModel):
    qr_code_bs64: str | None = None
