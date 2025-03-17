from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncConnection

from app.depedencies.database import get_async_conn, get_async_transaction_conn
from app.depedencies.rate_limiter import (
    critical_limit,
    limiter,
)
from app.helpers.response_api import JsonResponse
from app.schemas.users import (
    CreateUserPayload,
    CreateUserResponse,
    SignInPayload,
    SignInResponse,
)
from app.services.auth import AuthService


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


@router.post(
    "/sign-up",
    response_model=JsonResponse[CreateUserResponse, None],
    description="Register a new user with 2FA.",
)
@limiter.limit(critical_limit)
async def sign_up(
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
    content = JsonResponse(
        data={
            "qr_code_bs64": qr_code_bs64,
            "user": user_detail,
        },
        message="Success register user",
        status_code=status.HTTP_201_CREATED,
    )
    return JSONResponse(
        content=jsonable_encoder(content),
        status_code=status.HTTP_201_CREATED,
    )


@router.post(
    "/sign-in",
    response_model=JsonResponse[SignInResponse, None],
)
@limiter.limit(critical_limit)
async def sign_in(
    request: Request,
    response: Response,
    payload: Annotated[SignInPayload, Form()],
    connection: Annotated[AsyncConnection, Depends(get_async_conn)],
) -> JsonResponse[SignInResponse, None]:
    """Asynchronously sign in a user with Multi-Factor Authentication (MFA) enabled 🔐."""
    auth_service: AuthService = request.state.auth_service
    signin_response, cookies_refresh = await auth_service.sign_in(
        payload=payload,
        connection=connection,
    )

    if cookies_refresh:
        response.set_cookie(**cookies_refresh)

    msg = (
        "Sign in successful"
        if signin_response.mfa_required is False
        else "MFA verification required - temporary token issued"
    )
    status_code = status.HTTP_200_OK if signin_response.mfa_required is False else status.HTTP_202_ACCEPTED

    content = JsonResponse(
        data=signin_response,
        message=msg,
        status_code=status_code,
    )

    return JSONResponse(
        content=jsonable_encoder(content),
        status_code=status_code,
    )
