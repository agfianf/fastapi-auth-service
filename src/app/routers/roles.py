from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncConnection

from app.depedencies.auth import PERMISSION_SUPERADMIN
from app.depedencies.database import get_async_conn, get_async_transaction_conn
from app.depedencies.rate_limiter import default_limit, limiter
from app.helpers.response_api import JsonResponse, MetaResponse
from app.schemas.roles.base import RoleBase
from app.schemas.roles.payload import CreateRole, UpdateRole
from app.schemas.roles.response import CreateRoleResponse, UpdateRoleResponse
from app.schemas.users import UserMembershipQueryReponse
from app.schemas.users.admin.payload import SortOrder
from app.services.roles import RoleService


router = APIRouter(
    prefix="/api/v1/roles",
    tags=["Roles Management"],
)


@router.get(
    "",
    response_model=JsonResponse[list[RoleBase], MetaResponse],
    description="List all roles with pagination.",
)
@limiter.limit(default_limit)
async def get_all_roles(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_SUPERADMIN] = None,  # noqa: ARG001
    connection: Annotated[AsyncConnection, Depends(get_async_conn)] = None,
) -> JsonResponse[list[RoleBase], MetaResponse]:
    """List all roles with pagination."""
    role_service: RoleService = request.state.role_service
    roles, meta = await role_service.fetch_all_roles(
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=roles,
        message="Successfully retrieved roles",
        status_code=status_code,
        meta=meta,
    )


@router.get(
    "/{role_id}",
    response_model=JsonResponse[RoleBase, None],
    description="Get role details by ID.",
)
@limiter.limit(default_limit)
async def get_role_by_id(
    request: Request,
    response: Response,
    role_id: int,
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_SUPERADMIN] = None,  # noqa: ARG001
    connection: Annotated[AsyncConnection, Depends(get_async_conn)] = None,
) -> JsonResponse[RoleBase, None]:
    """Get role details by ID."""
    role_service: RoleService = request.state.role_service
    role = await role_service.fetch_role_by_id(
        role_id=role_id,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=role,
        message="Successfully retrieved role",
        status_code=status_code,
    )


@router.post(
    "",
    response_model=JsonResponse[CreateRoleResponse, None],
    description="Create a new role.",
)
@limiter.limit(default_limit)
async def create_role(
    request: Request,
    response: Response,
    payload: Annotated[CreateRole, Form()],
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_SUPERADMIN] = None,
    connection: Annotated[AsyncConnection, Depends(get_async_transaction_conn)] = None,
) -> JsonResponse[CreateRoleResponse, None]:
    """Create a new role."""
    role_service: RoleService = request.state.role_service
    role = await role_service.create_role(
        current_user=jwt_data[0],
        payload=payload,
        connection=connection,
    )

    status_code = status.HTTP_201_CREATED
    response.status_code = status_code
    return JsonResponse(
        data=role,
        message="Successfully created role",
        status_code=status_code,
    )


@router.put(
    "/{role_id}",
    response_model=JsonResponse[UpdateRoleResponse, None],
    description="Update an existing role.",
)
@limiter.limit(default_limit)
async def update_role(
    request: Request,
    response: Response,
    role_id: int,
    payload: Annotated[UpdateRole, Form()],
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_SUPERADMIN] = None,
    connection: Annotated[AsyncConnection, Depends(get_async_transaction_conn)] = None,
) -> JsonResponse[UpdateRoleResponse, None]:
    """Update an existing role."""
    role_service: RoleService = request.state.role_service
    role = await role_service.update_role(
        current_user=jwt_data[0],
        role_id=role_id,
        payload=payload,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=role,
        message="Successfully updated role",
        status_code=status_code,
    )


@router.delete(
    "/{role_id}",
    response_model=JsonResponse[None, None],
    description="Delete a role.",
)
@limiter.limit(default_limit)
async def delete_role(
    request: Request,
    response: Response,
    role_id: int,
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_SUPERADMIN] = None,
    connection: Annotated[AsyncConnection, Depends(get_async_transaction_conn)] = None,
) -> JsonResponse[None, None]:
    """Delete a role."""
    role_service: RoleService = request.state.role_service
    success = await role_service.delete_role(
        current_user=jwt_data[0],
        role_id=role_id,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=None,
        success=success,
        message="Successfully deleted role",
        status_code=status_code,
    )
