from sqlalchemy import Insert, Select, Update, delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from app.helpers.error_database import query_exceptions_handler
from app.helpers.response_api import MetaResponse
from app.models.business_roles import business_roles_table
from app.schemas.business_roles.base import BusinessRoleBase
from app.schemas.business_roles.payload import CreateBusinessRole, UpdateBusinessRole
from app.schemas.users.admin.payload import SortOrder


class BusinessRoleStatements:
    @staticmethod
    def get_business_role_by_id(business_role_id: int) -> Select:
        """Generate query to get business role by ID."""
        stmt = select(business_roles_table).where(
            business_roles_table.c.id == business_role_id, business_roles_table.c.deleted_at.is_(None)
        )
        return stmt

    @staticmethod
    def get_all_business_roles(
        page: int = 1,
        limit: int = 10,
        sort_by: str = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> tuple[Select, Select]:
        """Generate query to get all business roles with pagination."""
        # Base query
        stmt = select(business_roles_table).where(business_roles_table.c.deleted_at.is_(None))

        # Sorting
        sort_column = getattr(business_roles_table.c, sort_by, business_roles_table.c.created_at)
        stmt = stmt.order_by(sort_column.asc()) if sort_order == SortOrder.ASC else stmt.order_by(sort_column.desc())

        # Pagination
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)

        # Count query
        count_stmt = (
            select(func.count()).select_from(business_roles_table).where(business_roles_table.c.deleted_at.is_(None))
        )

        return stmt, count_stmt

    @staticmethod
    def create_business_role(payload: CreateBusinessRole, executed_by: str) -> Insert:
        """Generate query to create a new business role."""
        values = payload.transform()
        values["created_by"] = executed_by
        values["updated_by"] = executed_by
        stmt = insert(business_roles_table).values(**values).returning(*business_roles_table.c)
        return stmt

    @staticmethod
    def update_business_role(business_role_id: int, payload: UpdateBusinessRole, executed_by: str) -> Update:
        """Generate query to update an existing business role."""
        values = payload.transform()
        values["updated_by"] = executed_by
        stmt = (
            update(business_roles_table)
            .where(business_roles_table.c.id == business_role_id, business_roles_table.c.deleted_at.is_(None))
            .values(**values)
            .returning(*business_roles_table.c)
        )
        return stmt

    @staticmethod
    def delete_business_role(business_role_id: int, executed_by: str) -> Update:
        """Generate query to soft delete a business role."""
        stmt = (
            update(business_roles_table)
            .where(business_roles_table.c.id == business_role_id, business_roles_table.c.deleted_at.is_(None))
            .values(deleted_at=func.now(), deleted_by=executed_by)
            .returning(business_roles_table.c.id)
        )
        return stmt

    @staticmethod
    def hard_delete_business_role(business_role_id: int) -> Update:
        """Generate query to hard delete a business role (for testing only)."""
        stmt = (
            delete(business_roles_table)
            .where(business_roles_table.c.id == business_role_id)
            .returning(business_roles_table.c.id)
        )
        return stmt


class BusinessRoleAsyncRepositories:
    @staticmethod
    @query_exceptions_handler
    async def get_business_role_by_id(
        connection: AsyncConnection,
        business_role_id: int,
    ) -> BusinessRoleBase | None:
        """Get business role by ID."""
        stmt = BusinessRoleStatements.get_business_role_by_id(business_role_id=business_role_id)
        result = await connection.execute(stmt)
        business_role = result.mappings().first()
        if not business_role:
            return None
        return BusinessRoleBase.model_validate(dict(business_role))

    @staticmethod
    @query_exceptions_handler
    async def get_all_business_roles(
        connection: AsyncConnection,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> tuple[list[BusinessRoleBase], MetaResponse]:
        """Get all business roles with pagination."""
        stmt, count_stmt = BusinessRoleStatements.get_all_business_roles(
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        result = await connection.execute(stmt)
        business_role_rows = result.mappings().all()

        count_result = await connection.execute(count_stmt)
        total_items = count_result.scalar_one()
        total_pages = (total_items + limit - 1) // limit if limit > 0 else 0

        business_roles = [BusinessRoleBase.model_validate(dict(row)) for row in business_role_rows]

        meta = MetaResponse(
            current_page=page,
            page_size=len(business_roles),
            prev_page=page > 1,
            next_page=page < total_pages,
            total_pages=total_pages,
            total_items=total_items,
        )

        return business_roles, meta

    @staticmethod
    @query_exceptions_handler
    async def create_business_role(
        connection: AsyncConnection,
        payload: CreateBusinessRole,
        executed_by: str,
    ) -> BusinessRoleBase:
        """Create a new business role."""
        stmt = BusinessRoleStatements.create_business_role(payload=payload, executed_by=executed_by)
        result = await connection.execute(stmt)
        new_business_role = result.mappings().first()
        return BusinessRoleBase.model_validate(dict(new_business_role))

    @staticmethod
    @query_exceptions_handler
    async def update_business_role(
        connection: AsyncConnection,
        business_role_id: int,
        payload: UpdateBusinessRole,
        executed_by: str,
    ) -> BusinessRoleBase | None:
        """Update an existing business role."""
        stmt = BusinessRoleStatements.update_business_role(
            business_role_id=business_role_id, payload=payload, executed_by=executed_by
        )
        result = await connection.execute(stmt)
        updated_business_role = result.mappings().first()
        if not updated_business_role:
            return None
        return BusinessRoleBase.model_validate(dict(updated_business_role))

    @staticmethod
    @query_exceptions_handler
    async def delete_business_role(
        connection: AsyncConnection,
        business_role_id: int,
    ) -> bool:
        """Hard delete a business role."""
        stmt = BusinessRoleStatements.hard_delete_business_role(
            business_role_id=business_role_id,
        )
        result = await connection.execute(stmt)
        return result.scalar_one_or_none() is not None
