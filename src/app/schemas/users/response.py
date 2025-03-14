from pydantic import BaseModel

from app.schemas.users.query import CreateUserQueryResponse


class CreateUserResponse(BaseModel):
    qr_code_bs64: str | None = None
    user: CreateUserQueryResponse
