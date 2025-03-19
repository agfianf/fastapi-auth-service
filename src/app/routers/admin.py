from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncConnection

from app.depedencies.auth import PERMISSION_ADMIN
from app.depedencies.database import get_async_conn
from app.depedencies.rate_limiter import default_limit, limiter
from app.helpers.response_api import JsonResponse, MetaResponse
from app.schemas.users import UserMembershipQueryReponse
from app.schemas.users.admin.payload import GetUsersPayload
from app.services.admin import AdminService


router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admininstration"],
)


@router.get(
    "",
    response_model=JsonResponse[list[UserMembershipQueryReponse], MetaResponse],
    description="Register a new user with 2FA.",
)
@limiter.limit(default_limit)
async def get_list_users(
    request: Request,
    response: Response,
    payload: Annotated[GetUsersPayload, Query()],
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_ADMIN],
    connection: Annotated[AsyncConnection, Depends(get_async_conn)],
) -> JsonResponse[list[UserMembershipQueryReponse], MetaResponse]:
    """List all users."""
    admin_service: AdminService = request.state.admin_service
    users, meta = await admin_service.fetch_user_list(
        current_user=jwt_data[0],
        payload=payload,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=users,
        message="Successfully get list of users",
        status_code=status_code,
        meta=meta,
    )
