from typing import Annotated

from fastapi import APIRouter, Body, Depends, Form, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncConnection
from uuid_utils.compat import UUID

from app.depedencies.auth import PERMISSION_ADMIN
from app.depedencies.database import get_async_conn, get_async_transaction_conn
from app.depedencies.rate_limiter import default_limit, limiter
from app.helpers.response_api import JsonResponse, MetaResponse
from app.schemas.users import UserMembershipQueryReponse
from app.schemas.users.admin.payload import GetUsersPayload, UpdateUserByAdminPayload, UpdateUserServicesPayload
from app.services.admin import AdminService


router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admininstration"],
)


@router.get(
    "/users",
    response_model=JsonResponse[list[UserMembershipQueryReponse], MetaResponse],
    description="List all users with filtering and pagination.",
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


@router.get(
    "/users/{user_uuid}",
    response_model=JsonResponse[UserMembershipQueryReponse, None],
    description="Get user details.",
)
@limiter.limit(default_limit)
async def get_user_details(
    request: Request,
    response: Response,
    user_uuid: UUID,
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_ADMIN],
    connection: Annotated[AsyncConnection, Depends(get_async_conn)],
) -> JsonResponse[UserMembershipQueryReponse, None]:
    """Get user details."""
    admin_service: AdminService = request.state.admin_service
    user = await admin_service.fetch_user_details(
        current_user=jwt_data[0],
        user_uuid=user_uuid,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=user,
        message="Successfully get user details",
        status_code=status_code,
    )


@router.put(
    "/users/{user_uuid}",
    response_model=JsonResponse[None, None],
    description="Update user details.",
)
@limiter.limit(default_limit)
async def update_user_details(
    request: Request,
    response: Response,
    user_uuid: UUID,
    payload: Annotated[UpdateUserByAdminPayload, Form()],
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_ADMIN],
    connection: Annotated[AsyncConnection, Depends(get_async_transaction_conn)],
) -> JsonResponse[None, None]:
    """Update targeted user details.

    - ✏️ **Editable fields:** `role`, `active` and _should be **soon**_
    `company_id / mills_id`.<br>
    - 🚫 **Non-editable fields:** password, name, email, and username.
    """
    admin_service: AdminService = request.state.admin_service

    await admin_service.update_user_details(
        current_user=jwt_data[0],
        user_uuid=user_uuid,
        payload=payload,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=None,
        message="Successfully updated user details",
        status_code=status_code,
    )


@router.delete(
    "/users/{user_uuid}",
    response_model=JsonResponse[None, None],
    description="Delete user.",
)
@limiter.limit(default_limit)
async def delete_user(
    request: Request,
    response: Response,
    user_uuid: UUID,
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_ADMIN],
    connection: Annotated[AsyncConnection, Depends(get_async_transaction_conn)],
) -> JsonResponse[None, None]:
    """Delete targeted user."""
    admin_service: AdminService = request.state.admin_service

    await admin_service.delete_user(
        current_user=jwt_data[0],
        user_uuid=user_uuid,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=None,
        message="Successfully deleted user",
        status_code=status_code,
    )


@router.put(
    "/users/{user_uuid}/services",
    response_model=JsonResponse[None, None],
    description="Update user service mappings.",
)
@limiter.limit(default_limit)
async def update_user_services(
    request: Request,
    response: Response,
    user_uuid: UUID,
    payload: Annotated[UpdateUserServicesPayload, Body()],
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_ADMIN],
    connection: Annotated[AsyncConnection, Depends(get_async_transaction_conn)],
) -> JsonResponse[None, None]:
    """Update service mappings for a user.

    - 📝 This endpoint replaces all existing service mappings for the user
    - Each mapping consists of a service UUID, role ID, and active status
    - A user can have multiple service mappings with different roles
    """
    admin_service: AdminService = request.state.admin_service

    await admin_service.update_user_services(
        current_user=jwt_data[0],
        user_uuid=user_uuid,
        services=payload.services,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=None,
        message="Successfully updated user service mappings",
        status_code=status_code,
    )
