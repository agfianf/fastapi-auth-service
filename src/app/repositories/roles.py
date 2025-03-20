from sqlalchemy import Insert, Select, Update, delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from app.helpers.error_database import query_exceptions_handler
from app.helpers.response_api import MetaResponse
from app.models.roles import roles_table
from app.schemas.roles.base import RoleBase
from app.schemas.roles.payload import CreateRole, UpdateRole
from app.schemas.users.admin.payload import SortOrder


class RoleStatements:
    @staticmethod
    def get_role_by_id(role_id: int) -> Select:
        """Generate query to get role by ID."""
        stmt = select(roles_table).where(roles_table.c.id == role_id, roles_table.c.deleted_at.is_(None))
        return stmt

    @staticmethod
    def get_all_roles(
        page: int = 1,
        limit: int = 10,
        sort_by: str = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> tuple[Select, Select]:
        """Generate query to get all roles with pagination."""
        # Base query
        stmt = select(roles_table).where(roles_table.c.deleted_at.is_(None))

        # Sorting
        sort_column = getattr(roles_table.c, sort_by, roles_table.c.created_at)
        stmt = stmt.order_by(sort_column.asc()) if sort_order == SortOrder.ASC else stmt.order_by(sort_column.desc())

        # Pagination
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)

        # Count query
        count_stmt = select(func.count()).select_from(roles_table).where(roles_table.c.deleted_at.is_(None))

        return stmt, count_stmt

    @staticmethod
    def create_role(payload: CreateRole, executed_by: str) -> Insert:
        """Generate query to create a new role."""
        values = payload.transform()
        values["created_by"] = executed_by
        values["updated_by"] = executed_by
        stmt = insert(roles_table).values(**values).returning(*roles_table.c)
        return stmt

    @staticmethod
    def update_role(role_id: int, payload: UpdateRole, executed_by: str) -> Update:
        """Generate query to update an existing role."""
        values = payload.transform()
        values["updated_by"] = executed_by
        stmt = (
            update(roles_table)
            .where(roles_table.c.id == role_id, roles_table.c.deleted_at.is_(None))
            .values(**values)
            .returning(*roles_table.c)
        )
        return stmt

    @staticmethod
    def delete_role(role_id: int, executed_by: str) -> Update:
        """Generate query to soft delete a role."""
        stmt = (
            update(roles_table)
            .where(roles_table.c.id == role_id, roles_table.c.deleted_at.is_(None))
            .values(deleted_at=func.now(), deleted_by=executed_by)
            .returning(roles_table.c.id)
        )
        return stmt

    @staticmethod
    def hard_delete_role(role_id: int) -> Update:
        """Generate query to hard delete a role (for testing only)."""
        stmt = delete(roles_table).where(roles_table.c.id == role_id).returning(roles_table.c.id)
        return stmt


class RoleAsyncRepositories:
    @staticmethod
    @query_exceptions_handler
    async def get_role_by_id(
        connection: AsyncConnection,
        role_id: int,
    ) -> RoleBase | None:
        """Get role by ID."""
        stmt = RoleStatements.get_role_by_id(role_id=role_id)
        result = await connection.execute(stmt)
        role = result.mappings().first()
        if not role:
            return None
        return RoleBase.model_validate(dict(role))

    @staticmethod
    @query_exceptions_handler
    async def get_all_roles(
        connection: AsyncConnection,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> tuple[list[RoleBase], MetaResponse]:
        """Get all roles with pagination."""
        stmt, count_stmt = RoleStatements.get_all_roles(
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        result = await connection.execute(stmt)
        role_rows = result.mappings().all()

        count_result = await connection.execute(count_stmt)
        total_items = count_result.scalar_one()
        total_pages = (total_items + limit - 1) // limit if limit > 0 else 0

        roles = [RoleBase.model_validate(dict(row)) for row in role_rows]

        meta = MetaResponse(
            current_page=page,
            page_size=len(roles),
            prev_page=page > 1,
            next_page=page < total_pages,
            total_pages=total_pages,
            total_items=total_items,
        )

        return roles, meta

    @staticmethod
    @query_exceptions_handler
    async def create_role(
        connection: AsyncConnection,
        payload: CreateRole,
        executed_by: str,
    ) -> RoleBase:
        """Create a new role."""
        stmt = RoleStatements.create_role(payload=payload, executed_by=executed_by)
        result = await connection.execute(stmt)
        new_role = result.mappings().first()
        return RoleBase.model_validate(dict(new_role))

    @staticmethod
    @query_exceptions_handler
    async def update_role(
        connection: AsyncConnection,
        role_id: int,
        payload: UpdateRole,
        executed_by: str,
    ) -> RoleBase | None:
        """Update an existing role."""
        stmt = RoleStatements.update_role(role_id=role_id, payload=payload, executed_by=executed_by)
        result = await connection.execute(stmt)
        updated_role = result.mappings().first()
        if not updated_role:
            return None
        return RoleBase.model_validate(dict(updated_role))

    @staticmethod
    @query_exceptions_handler
    async def delete_role(
        connection: AsyncConnection,
        role_id: int,
        executed_by: str,
    ) -> bool:
        """Soft delete a role."""
        stmt = RoleStatements.delete_role(role_id=role_id, executed_by=executed_by)
        result = await connection.execute(stmt)
        return result.scalar_one_or_none() is not None
