from sqlalchemy.ext.asyncio import AsyncConnection
from uuid_utils.compat import UUID

from app.exceptions.services import (
    ServiceCreationFailedException,
    ServiceDeletionFailedException,
    ServiceNameAlreadyExistsException,
    ServiceNotFoundException,
    ServiceUpdateFailedException,
)
from app.helpers.response_api import MetaResponse
from app.integrations.redis import RedisHelper
from app.repositories.services import ServiceAsyncRepositories
from app.schemas.services.base import ServiceBase
from app.schemas.services.payload import CreateService, GetServicesPayload, UpdateService
from app.schemas.users import UserMembershipQueryReponse


class ServiceService:
    def __init__(
        self,
        repo_services: ServiceAsyncRepositories,
        redis: RedisHelper,
    ) -> None:
        self.repo_services = repo_services
        self.redis = redis

    async def fetch_service_by_uuid(
        self,
        service_uuid: UUID,
        connection: AsyncConnection,
    ) -> ServiceBase:
        """Get service by UUID."""
        service = await self.repo_services.get_service_by_uuid(
            connection=connection,
            service_uuid=service_uuid,
        )

        if service is None:
            raise ServiceNotFoundException()

        return service

    async def fetch_all_services(
        self,
        payload: GetServicesPayload,
        connection: AsyncConnection,
    ) -> tuple[list[ServiceBase], MetaResponse]:
        """Get all services with filtering and pagination."""
        services, meta = await self.repo_services.get_all_services(
            connection=connection,
            payload=payload,
        )

        return services, meta

    async def create_service(
        self,
        current_user: UserMembershipQueryReponse,
        payload: CreateService,
        connection: AsyncConnection,
    ) -> ServiceBase:
        """Create a new service."""
        service = await self.repo_services.create_service(
            connection=connection,
            payload=payload,
            executed_by=current_user.email,
        )

        if service is None:
            raise ServiceCreationFailedException()

        return service

    async def update_service(
        self,
        current_user: UserMembershipQueryReponse,
        service_uuid: UUID,
        payload: UpdateService,
        connection: AsyncConnection,
    ) -> ServiceBase:
        """Update an existing service."""
        # Check if service exists
        await self.fetch_service_by_uuid(service_uuid=service_uuid, connection=connection)

        # If name is being updated, check if it already exists
        if payload.name is not None:
            existing_service = await self.repo_services.get_service_by_name(
                connection=connection,
                name=payload.name,
            )
            if existing_service is not None and existing_service.uuid != service_uuid:
                raise ServiceNameAlreadyExistsException()

        updated_service = await self.repo_services.update_service(
            connection=connection,
            service_uuid=service_uuid,
            payload=payload,
            executed_by=current_user.email,
        )

        if updated_service is None:
            raise ServiceUpdateFailedException()

        return updated_service

    async def delete_service(
        self,
        current_user: UserMembershipQueryReponse,
        service_uuid: UUID,
        connection: AsyncConnection,
    ) -> bool:
        """Delete a service."""
        # Check if service exists
        await self.fetch_service_by_uuid(service_uuid=service_uuid, connection=connection)

        success = await self.repo_services.soft_delete_service(
            connection=connection,
            service_uuid=service_uuid,
            executed_by=current_user.email,
        )

        if not success:
            raise ServiceDeletionFailedException()

        return success
