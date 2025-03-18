from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Form, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncConnection

from app.depedencies.auth import JWTBearer
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
    UserMembershipQueryReponse,
    VerifyMFAResponse,
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
    response: Response,
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

    status_code = status.HTTP_201_CREATED
    response.status_code = status_code
    return JsonResponse(
        data={
            "qr_code_bs64": qr_code_bs64,
            "user": user_detail,
        },
        message="Success register user",
        status_code=status_code,
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

    response.status_code = status_code
    return JsonResponse(
        data=signin_response,
        message=msg,
        status_code=status_code,
    )


@router.delete("/sign-out", response_model=JsonResponse[dict[str, bool], None])
@limiter.limit(critical_limit)
async def sign_out(
    request: Request,
    response: Response,
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], Depends(JWTBearer())],
    refresh_token_app: str = Cookie(...),
) -> JsonResponse[dict[str, bool], None]:
    """Sign out user and revoke tokens.

    Parameters
    ----------
    request : Request
        The FastAPI request object
    response : Response
        The FastAPI response object
    jwt_data : tuple[UserMembershipQueryReponse, str]
        A tuple containing user membership data and the access token
    refresh_token_app : str
        The refresh token from cookies

    Returns
    -------
    JsonResponse
        Response confirming logout with cookie cleanup

    """
    auth_service: AuthService = request.state.auth_service

    _, access_token = jwt_data
    is_revoked, delete_cookies = await auth_service.sign_out(
        access_token=access_token,
        refresh_token_app=refresh_token_app,
    )

    response.delete_cookie(**delete_cookies)
    response.status_code = status.HTTP_200_OK

    return JsonResponse(
        data=is_revoked,
        message="Successfully signed out",
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/verify-mfa",
    response_model=JsonResponse[VerifyMFAResponse, None],
)
@limiter.limit(critical_limit)
async def verify_mfa(  # noqa: N802
    request: Request,
    response: Response,
    username: Annotated[str, Form(...)],
    mfa_token: Annotated[str, Form(...)],
    mfa_code: Annotated[str, Form(...)],
    connection: Annotated[
        AsyncConnection,
        Depends(get_async_transaction_conn),
    ],
) -> JsonResponse[VerifyMFAResponse, None]:
    auth_service: AuthService = request.state.auth_service
    access_token, cookies_refresh = await auth_service.verify_mfa(
        mfa_token=mfa_token,
        mfa_code=mfa_code,
        username=username,
        connection=connection,
    )

    response.set_cookie(**cookies_refresh)
    response.status_code = status.HTTP_200_OK
    return JsonResponse(
        data=access_token,
        message="Successfully signed in and verified MFA",
        status_code=status.HTTP_200_OK,
    )
