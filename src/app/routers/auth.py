from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncConnection

from app.depedencies.database import (  # noqa: F401
    get_async_transaction_conn,
)
from app.depedencies.rate_limiter import (
    critical_limit,
    limiter,
)
from app.helpers.response_api import JsonResponse
from app.schemas.users import CreateUserPayload, CreateUserResponse
from app.services.auth import AuthService


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post(
    "/sign-up",
    response_model=JsonResponse[CreateUserResponse, None],
    description="Register a new user with 2FA.",
)
@limiter.limit(critical_limit)
async def sign_up_with_mfa(
    request: Request,
    payload: Annotated[CreateUserPayload, Form()],
    connection: Annotated[
        AsyncConnection,
        Depends(get_async_transaction_conn),
    ],
) -> JsonResponse[CreateUserResponse, None]:
    """Asynchronously sign up a new user with Multi-Factor Authentication (MFA) enabled 🔐."""  # noqa: E501
    auth_service: AuthService = request.state.auth_service
    user_detail, qr_code_bs64 = await auth_service.sign_up(
        payload=payload,
        connection=connection,
    )
    return JsonResponse(
        data={
            "qr_code_bs64": qr_code_bs64,
            "user": user_detail,
        },
        message="Success register user",
        status_code=status.HTTP_201_CREATED,
    )
