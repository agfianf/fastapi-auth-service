from sqlalchemy import Select, Update, and_, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection
from uuid_utils.compat import UUID

from app.helpers.error_database import query_exceptions_handler
from app.helpers.response_api import MetaResponse
from app.models.services import services_table
from app.schemas.services.base import ServiceBase
from app.schemas.services.payload import CreateService, GetServicesPayload, UpdateService


class ServiceStatements:
    @staticmethod
    def get_service_by_uuid(service_uuid: UUID) -> Select:
        """Generate query to get service by UUID."""
        stmt = select(services_table).where(
            services_table.c.uuid == service_uuid, services_table.c.deleted_at.is_(None)
        )
        return stmt

    @staticmethod
    def get_service_by_name(name: str) -> Select:
        """Generate query to get service by name."""
        stmt = select(services_table).where(services_table.c.name == name, services_table.c.deleted_at.is_(None))
        return stmt

    @staticmethod
    def get_all_services(
        payload: GetServicesPayload,
    ) -> tuple[Select, Select]:
        """Generate query to get all services with filtering and pagination."""
        # Base query
        filters = [services_table.c.deleted_at.is_(None)]

        # Apply filters
        if payload.name:
            filters.append(services_table.c.name.ilike(f"%{payload.name}%"))

        if payload.is_active is not None:
            filters.append(services_table.c.is_active == payload.is_active)

        stmt = select(services_table).where(and_(*filters))

        # Sorting
        sort_by = payload.sort_by if hasattr(services_table.c, payload.sort_by) else "created_at"
        sort_column = getattr(services_table.c, sort_by)

        if payload.sort_order.lower() == "asc":
            stmt = stmt.order_by(sort_column.asc())
        else:
            stmt = stmt.order_by(sort_column.desc())

        # Pagination
        offset = (payload.page - 1) * payload.limit
        stmt = stmt.offset(offset).limit(payload.limit)

        # Count query
        count_stmt = select(func.count()).select_from(services_table).where(and_(*filters))

        return stmt, count_stmt

    @staticmethod
    def create_service(payload: CreateService, executed_by: str):
        """Generate query to create a new service."""
        values = payload.transform()
        values["created_by"] = executed_by
        values["updated_by"] = executed_by

        stmt = insert(services_table).values(**values).returning(*services_table.c)
        return stmt

    @staticmethod
    def update_service(service_uuid: UUID, payload: UpdateService, executed_by: str) -> Update:
        """Generate query to update a service."""
        values = payload.transform()
        values["updated_by"] = executed_by

        stmt = (
            update(services_table)
            .where(services_table.c.uuid == service_uuid, services_table.c.deleted_at.is_(None))
            .values(**values)
            .returning(*services_table.c)
        )
        return stmt

    @staticmethod
    def soft_delete_service(service_uuid: UUID, executed_by: str) -> Update:
        """Generate query to soft delete a service."""
        stmt = (
            update(services_table)
            .where(services_table.c.uuid == service_uuid, services_table.c.deleted_at.is_(None))
            .values(deleted_at=func.now(), deleted_by=executed_by)
            .returning(services_table.c.uuid)
        )
        return stmt


class ServiceAsyncRepositories:
    @staticmethod
    @query_exceptions_handler
    async def get_service_by_uuid(
        connection: AsyncConnection,
        service_uuid: UUID,
    ) -> ServiceBase | None:
        """Get service by UUID."""
        stmt = ServiceStatements.get_service_by_uuid(service_uuid=service_uuid)
        result = await connection.execute(stmt)
        service = result.mappings().first()

        if not service:
            return None

        return ServiceBase.model_validate(dict(service))

    @staticmethod
    @query_exceptions_handler
    async def get_service_by_name(
        connection: AsyncConnection,
        name: str,
    ) -> ServiceBase | None:
        """Get service by name."""
        stmt = ServiceStatements.get_service_by_name(name=name)
        result = await connection.execute(stmt)
        service = result.mappings().first()

        if not service:
            return None

        return ServiceBase.model_validate(dict(service))

    @staticmethod
    @query_exceptions_handler
    async def get_all_services(
        connection: AsyncConnection,
        payload: GetServicesPayload,
    ) -> tuple[list[ServiceBase], MetaResponse]:
        """Get all services with filtering and pagination."""
        stmt, count_stmt = ServiceStatements.get_all_services(payload=payload)

        result = await connection.execute(stmt)
        service_rows = result.mappings().all()

        count_result = await connection.execute(count_stmt)
        total_items = count_result.scalar_one()
        total_pages = (total_items + payload.limit - 1) // payload.limit if payload.limit > 0 else 0

        services = [ServiceBase.model_validate(dict(row)) for row in service_rows]

        meta = MetaResponse(
            current_page=payload.page,
            page_size=len(services),
            prev_page=payload.page > 1,
            next_page=payload.page < total_pages,
            total_pages=total_pages,
            total_items=total_items,
        )

        return services, meta

    @staticmethod
    @query_exceptions_handler
    async def create_service(
        connection: AsyncConnection,
        payload: CreateService,
        executed_by: str,
    ) -> ServiceBase:
        """Create a new service."""
        print("Creating service with payload:", payload)
        print("Executed by:", executed_by)
        stmt = ServiceStatements.create_service(payload=payload, executed_by=executed_by)
        result = await connection.execute(stmt)
        new_service = result.mappings().first()

        return ServiceBase.model_validate(dict(new_service))

    @staticmethod
    @query_exceptions_handler
    async def update_service(
        connection: AsyncConnection,
        service_uuid: UUID,
        payload: UpdateService,
        executed_by: str,
    ) -> ServiceBase | None:
        """Update an existing service."""
        stmt = ServiceStatements.update_service(service_uuid=service_uuid, payload=payload, executed_by=executed_by)
        result = await connection.execute(stmt)
        updated_service = result.mappings().first()

        if not updated_service:
            return None

        return ServiceBase.model_validate(dict(updated_service))

    @staticmethod
    @query_exceptions_handler
    async def soft_delete_service(
        connection: AsyncConnection,
        service_uuid: UUID,
        executed_by: str,
    ) -> bool:
        """Soft delete a service."""
        stmt = ServiceStatements.soft_delete_service(service_uuid=service_uuid, executed_by=executed_by)
        result = await connection.execute(stmt)

        return result.scalar_one_or_none() is not None
