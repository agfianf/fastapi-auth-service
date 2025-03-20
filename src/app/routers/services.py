from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncConnection
from uuid_utils.compat import UUID

from app.depedencies.auth import PERMISSION_ADMIN
from app.depedencies.database import get_async_conn, get_async_transaction_conn
from app.depedencies.rate_limiter import default_limit, limiter
from app.helpers.response_api import JsonResponse, MetaResponse
from app.schemas.services.base import ServiceBase
from app.schemas.services.payload import CreateService, GetServicesPayload, UpdateService
from app.schemas.services.response import CreateServiceResponse, UpdateServiceResponse
from app.schemas.users import UserMembershipQueryReponse
from app.services.services import ServiceService


router = APIRouter(
    prefix="/api/v1/services",
    tags=["Service Management"],
)


@router.get(
    "",
    response_model=JsonResponse[list[ServiceBase], MetaResponse],
    description="List all services with filtering and pagination.",
)
@limiter.limit(default_limit)
async def get_all_services(
    request: Request,
    response: Response,
    payload: Annotated[GetServicesPayload, Query()],
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_ADMIN],  # noqa: ARG001
    connection: Annotated[AsyncConnection, Depends(get_async_conn)],
) -> JsonResponse[list[ServiceBase], MetaResponse]:
    """List all services with filtering and pagination."""
    service_service: ServiceService = request.state.service_service
    services, meta = await service_service.fetch_all_services(
        payload=payload,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=services,
        message="Successfully retrieved services",
        status_code=status_code,
        meta=meta,
    )


@router.get(
    "/{service_uuid}",
    response_model=JsonResponse[ServiceBase, None],
    description="Get service details by UUID.",
)
@limiter.limit(default_limit)
async def get_service_by_uuid(
    request: Request,
    response: Response,
    service_uuid: UUID,
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_ADMIN],  # noqa: ARG001
    connection: Annotated[AsyncConnection, Depends(get_async_conn)],
) -> JsonResponse[ServiceBase, None]:
    """Get service details by UUID."""
    service_service: ServiceService = request.state.service_service
    service = await service_service.fetch_service_by_uuid(
        service_uuid=service_uuid,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=service,
        message="Successfully retrieved service",
        status_code=status_code,
    )


@router.post(
    "",
    response_model=JsonResponse[CreateServiceResponse, None],
    description="Create a new service.",
)
@limiter.limit(default_limit)
async def create_service(
    request: Request,
    response: Response,
    payload: Annotated[CreateService, Form()],
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_ADMIN],
    connection: Annotated[AsyncConnection, Depends(get_async_transaction_conn)],
) -> JsonResponse[CreateServiceResponse, None]:
    """Create a new service."""
    service_service: ServiceService = request.state.service_service
    service = await service_service.create_service(
        current_user=jwt_data[0],
        payload=payload,
        connection=connection,
    )

    status_code = status.HTTP_201_CREATED
    response.status_code = status_code
    return JsonResponse(
        data=service,
        message="Successfully created service",
        status_code=status_code,
    )


@router.put(
    "/{service_uuid}",
    response_model=JsonResponse[UpdateServiceResponse, None],
    description="Update an existing service.",
)
@limiter.limit(default_limit)
async def update_service(
    request: Request,
    response: Response,
    service_uuid: UUID,
    payload: Annotated[UpdateService, Form()],
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_ADMIN],
    connection: Annotated[AsyncConnection, Depends(get_async_transaction_conn)],
) -> JsonResponse[UpdateServiceResponse, None]:
    """Update an existing service."""
    service_service: ServiceService = request.state.service_service
    service = await service_service.update_service(
        current_user=jwt_data[0],
        service_uuid=service_uuid,
        payload=payload,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=service,
        message="Successfully updated service",
        status_code=status_code,
    )


@router.delete(
    "/{service_uuid}",
    response_model=JsonResponse[None, None],
    description="Delete a service.",
)
@limiter.limit(default_limit)
async def delete_service(
    request: Request,
    response: Response,
    service_uuid: UUID,
    jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], PERMISSION_ADMIN],
    connection: Annotated[AsyncConnection, Depends(get_async_transaction_conn)],
) -> JsonResponse[None, None]:
    """Delete a service."""
    service_service: ServiceService = request.state.service_service
    success = await service_service.delete_service(
        current_user=jwt_data[0],
        service_uuid=service_uuid,
        connection=connection,
    )

    status_code = status.HTTP_200_OK
    response.status_code = status_code
    return JsonResponse(
        data=None,
        success=success,
        message="Successfully deleted service",
        status_code=status_code,
    )
