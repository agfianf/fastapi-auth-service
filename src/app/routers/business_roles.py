from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncConnection

from app.depedencies.auth import PERMISSION_SUPERADMIN
from app.depedencies.database import get_async_conn, get_async_transaction_conn
from app.depedencies.rate_limiter import default_limit, limiter
from app.helpers.response_api import JsonResponse, MetaResponse
from app.schemas.business_roles.base import BusinessRoleBase
from app.schemas.business_roles.payload import CreateBusinessRole, UpdateBusinessRole
from app.schemas.business_roles.response import CreateBusinessRoleResponse, UpdateBusinessRoleResponse
from app.schemas.users import UserMembershipQueryReponse
from app.schemas.users.admin.payload import SortOrder
from app.services.business_roles import BusinessRoleService


router = APIRouter(
    prefix="/api/v1/business-roles",
    tags=["Business Roles Management"],
)


@router.get(
    "",
    response_model=JsonResponse[list[BusinessRoleBase], MetaResponse],
    description="List all business roles with pagination.",
)
@limiter.limit(default_limit)
async def get_all_business_roles(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_SUPERADMIN] = None,  # noqa: ARG001
    connection: Annotated[AsyncConnection, Depends(get_async_conn)] = None,
) -> JsonResponse[list[BusinessRoleBase], MetaResponse]:
    """List all business roles with pagination."""
    business_role_service: BusinessRoleService = request.state.business_role_service
    business_roles, meta = await business_role_service.fetch_all_business_roles(
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=business_roles,
        message="Successfully retrieved business roles",
        status_code=status_code,
        meta=meta,
    )


@router.get(
    "/{business_role_id}",
    response_model=JsonResponse[BusinessRoleBase, None],
    description="Get business role details by ID.",
)
@limiter.limit(default_limit)
async def get_business_role_by_id(
    request: Request,
    response: Response,
    business_role_id: int,
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_SUPERADMIN] = None,  # noqa: ARG001
    connection: Annotated[AsyncConnection, Depends(get_async_conn)] = None,
) -> JsonResponse[BusinessRoleBase, None]:
    """Get business role details by ID."""
    business_role_service: BusinessRoleService = request.state.business_role_service
    business_role = await business_role_service.fetch_business_role_by_id(
        business_role_id=business_role_id,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=business_role,
        message="Successfully retrieved business role",
        status_code=status_code,
    )


@router.post(
    "",
    response_model=JsonResponse[CreateBusinessRoleResponse, None],
    description="Create a new business role.",
)
@limiter.limit(default_limit)
async def create_business_role(
    request: Request,
    response: Response,
    payload: Annotated[CreateBusinessRole, Form()],
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_SUPERADMIN] = None,
    connection: Annotated[AsyncConnection, Depends(get_async_transaction_conn)] = None,
) -> JsonResponse[CreateBusinessRoleResponse, None]:
    """Create a new business role."""
    business_role_service: BusinessRoleService = request.state.business_role_service
    business_role = await business_role_service.create_business_role(
        current_user=jwt_data[0],
        payload=payload,
        connection=connection,
    )

    status_code = status.HTTP_201_CREATED
    response.status_code = status_code
    return JsonResponse(
        data=business_role,
        message="Successfully created business role",
        status_code=status_code,
    )


@router.put(
    "/{business_role_id}",
    response_model=JsonResponse[UpdateBusinessRoleResponse, None],
    description="Update an existing business role.",
)
@limiter.limit(default_limit)
async def update_business_role(
    request: Request,
    response: Response,
    business_role_id: int,
    payload: Annotated[UpdateBusinessRole, Form()],
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_SUPERADMIN] = None,
    connection: Annotated[AsyncConnection, Depends(get_async_transaction_conn)] = None,
) -> JsonResponse[UpdateBusinessRoleResponse, None]:
    """Update an existing business role."""
    business_role_service: BusinessRoleService = request.state.business_role_service
    business_role = await business_role_service.update_business_role(
        current_user=jwt_data[0],
        business_role_id=business_role_id,
        payload=payload,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=business_role,
        message="Successfully updated business role",
        status_code=status_code,
    )


@router.delete(
    "/{business_role_id}",
    response_model=JsonResponse[None, None],
    description="Delete a business role.",
)
@limiter.limit(default_limit)
async def delete_business_role(
    request: Request,
    response: Response,
    business_role_id: int,
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_SUPERADMIN] = None,  # noqa: ARG001
    connection: Annotated[AsyncConnection, Depends(get_async_transaction_conn)] = None,
) -> JsonResponse[None, None]:
    """Delete a business role."""
    business_role_service: BusinessRoleService = request.state.business_role_service
    success = await business_role_service.delete_business_role(
        business_role_id=business_role_id,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=None,
        success=success,
        message="Successfully deleted business role",
        status_code=status_code,
    )
