from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Form, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncConnection

from app.depedencies.auth import jwt_bearer
from app.depedencies.database import get_async_conn, get_async_transaction_conn
from app.depedencies.rate_limiter import default_limit, limiter
from app.helpers.response_api import JsonResponse
from app.schemas.member import (
    MemberDetailsResponse,
    MFAQRCodeResponse,
    UpdateMemberPayload,
    UpdateMemberResponse,
    UpdateMFAPayload,
    UpdatePasswordPayload,
)
from app.schemas.member.response import UpdateMemberMFAResponse
from app.schemas.users import UserMembershipQueryReponse
from app.services.member import MemberService


router = APIRouter(
    prefix="/api/v1/me",
    tags=["Member"],
)


@router.get(
    "",
    response_model=JsonResponse[MemberDetailsResponse, None],
    description="Get current member details",
)
@limiter.limit(default_limit)
async def get_member_details(
    request: Request,
    response: Response,
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], Depends(jwt_bearer)],
    connection: Annotated[AsyncConnection, Depends(get_async_conn)],
) -> JsonResponse[MemberDetailsResponse, None]:
    """Get details of the currently authenticated member."""
    member_service: MemberService = request.state.member_service
    member = await member_service.fetch_member_details(
        user_uid=jwt_data[0].uuid,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=member,
        message="Successfully retrieved member details",
        status_code=status_code,
    )


@router.put(
    "/password",
    response_model=JsonResponse[UpdateMemberResponse, None],
    description="Update member password",
)
@limiter.limit(default_limit)
async def update_password(
    request: Request,
    response: Response,
    payload: Annotated[UpdatePasswordPayload, Form()],
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], Depends(jwt_bearer)],
    connection: Annotated[AsyncConnection, Depends(get_async_transaction_conn)],
    refresh_token_app: str = Cookie(...),
) -> JsonResponse[UpdateMemberResponse, None]:
    """Update the password of the currently authenticated member."""
    member_service: MemberService = request.state.member_service
    current_user, access_token = jwt_data

    result, cookies = await member_service.update_password(
        current_user=current_user,
        payload=payload,
        access_token=access_token,
        refresh_token=refresh_token_app,
        connection=connection,
    )

    response.set_cookie(**cookies)

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=result,
        message="Password updated successfully",
        status_code=status_code,
    )


@router.put(
    "/mfa",
    response_model=JsonResponse[UpdateMemberMFAResponse, None],
    description="Update MFA settings",
)
@limiter.limit(default_limit)
async def update_mfa(
    request: Request,
    response: Response,
    payload: Annotated[UpdateMFAPayload, Form()],
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], Depends(jwt_bearer)],
    connection: Annotated[AsyncConnection, Depends(get_async_transaction_conn)],
    refresh_token_app: str = Cookie(...),
) -> JsonResponse[UpdateMemberMFAResponse, None]:
    """Enable or disable Multi-Factor Authentication for the member."""
    member_service: MemberService = request.state.member_service
    current_user, access_token = jwt_data

    result, cookies = await member_service.update_mfa(
        current_user=current_user,
        payload=payload,
        access_token=access_token,
        refresh_token=refresh_token_app,
        connection=connection,
    )

    response.set_cookie(**cookies)

    status_code = status.HTTP_200_OK
    response.status_code = status_code

    msg = "MFA enabled successfully" if payload.mfa_enabled else "MFA disabled successfully"
    return JsonResponse(
        data=result,
        message=msg,
        status_code=status_code,
    )


@router.put(
    "",
    response_model=JsonResponse[UpdateMemberResponse, None],
    description="Update member profile",
)
@limiter.limit(default_limit)
async def update_profile(
    request: Request,
    response: Response,
    payload: Annotated[UpdateMemberPayload, Form()],
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], Depends(jwt_bearer)],
    connection: Annotated[AsyncConnection, Depends(get_async_transaction_conn)],
    refresh_token_app: str = Cookie(...),
) -> JsonResponse[UpdateMemberResponse, None]:
    """Update the profile information of the currently authenticated member."""
    member_service: MemberService = request.state.member_service
    current_user, access_token = jwt_data

    result, cookies = await member_service.update_profile(
        current_user=current_user,
        payload=payload,
        access_token=access_token,
        refresh_token=refresh_token_app,
        connection=connection,
    )

    # Set new refresh token cookie
    response.set_cookie(**cookies)

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=result,
        message="Profile updated successfully",
        status_code=status_code,
    )


@router.get(
    "/mfa/qrcode",
    response_model=JsonResponse[MFAQRCodeResponse, None],
    description="Get MFA QR code for setup",
)
@limiter.limit(default_limit)
async def get_mfa_qrcode(
    request: Request,
    response: Response,
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], Depends(jwt_bearer)],
    connection: Annotated[AsyncConnection, Depends(get_async_conn)],
) -> JsonResponse[MFAQRCodeResponse, None]:
    """Get a QR code for setting up MFA (before enabling it)."""
    member_service: MemberService = request.state.member_service

    result = await member_service.get_mfa_qrcode(
        current_user=jwt_data[0],
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=result,
        message="MFA QR code generated successfully",
        status_code=status_code,
    )
