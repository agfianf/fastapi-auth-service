from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncConnection
from uuid_utils.compat import UUID

from app.helpers.error_database import query_exceptions_handler
from app.helpers.response_api import MetaResponse
from app.models.roles import roles_table
from app.models.services import service_memberships_table, services_table
from app.models.users import users_table
from app.schemas.users.admin.payload import GetUsersPayload, SortOrder
from app.schemas.users.query import UserMembershipQueryReponse


class AdminStatement:
    @staticmethod
    def get_user_details(user_uuid: UUID, role: str):
        service_roles = roles_table.alias("service_roles")
        columns_select = [
            users_table.c.uuid,
            users_table.c.username,
            users_table.c.firstname,
            users_table.c.midname,
            users_table.c.lastname,
            users_table.c.email,
            users_table.c.phone,
            users_table.c.telegram,
            users_table.c.mfa_enabled,
            users_table.c.is_active,
            users_table.c.created_at,
            users_table.c.updated_at,
            users_table.c.deleted_at,
            roles_table.c.name.label("role"),
            services_table.c.uuid.label("service_uuid"),
            services_table.c.name.label("service_name"),
            services_table.c.description.label("service_description"),
            services_table.c.is_active.label("service_is_active"),
            service_memberships_table.c.is_active.label("member_is_active"),
            service_roles.c.name.label("service_role_name"),
        ]

        chain = (
            users_table.outerjoin(roles_table, users_table.c.role_id == roles_table.c.id)
            .outerjoin(
                service_memberships_table,
                users_table.c.uuid == service_memberships_table.c.user_uuid,
            )  # Join to service memberships
            .outerjoin(
                services_table,
                service_memberships_table.c.service_uuid == services_table.c.uuid,
            )  # Join to services
            .outerjoin(
                service_roles,
                service_memberships_table.c.role_id == service_roles.c.id,
            )
        )

        filters = []
        if role == "admin":
            # hide superadmin info from admin
            filters.append(users_table.c.role_id != 1)
        filters.append(users_table.c.deleted_at.is_(None))
        filters.append(users_table.c.uuid == user_uuid)

        stmt = select(*columns_select).select_from(chain).where(and_(*filters))

        return stmt

    @staticmethod
    def get_list_users(p: GetUsersPayload, role: str) -> tuple[Select, Select]:
        """Fetch all users."""
        filters = []

        if p.email:
            filters.append(users_table.c.email == p.email)

        if p.username:
            filters.append(users_table.c.username == p.username)

        if p.is_active is not None:
            filters.append(users_table.c.is_active == p.is_active)

        if p.roles:
            filters.append(roles_table.c.name.in_(p.roles))

        if p.is_deleted is not None:
            filters.append(
                users_table.c.deleted_at.is_(None) if not p.is_deleted else users_table.c.deleted_at.isnot(None)
            )

        if role == "admin":
            # hide superadmin from admin
            filters.append(users_table.c.role_id != 1)

        service_roles = roles_table.alias("service_roles")
        columns_select = [
            users_table.c.uuid,
            users_table.c.username,
            users_table.c.firstname,
            users_table.c.midname,
            users_table.c.lastname,
            users_table.c.email,
            users_table.c.phone,
            users_table.c.telegram,
            users_table.c.password_hash,
            users_table.c.mfa_enabled,
            users_table.c.mfa_secret,
            users_table.c.is_active,
            users_table.c.created_at,
            users_table.c.updated_at,
            users_table.c.deleted_at,
            roles_table.c.name.label("role"),
            services_table.c.uuid.label("service_uuid"),
            services_table.c.name.label("service_name"),
            services_table.c.description.label("service_description"),
            services_table.c.is_active.label("service_is_active"),
            service_memberships_table.c.is_active.label("member_is_active"),
            service_roles.c.name.label("service_role_name"),
        ]

        chain = (
            users_table.outerjoin(roles_table, users_table.c.role_id == roles_table.c.id)
            .outerjoin(
                service_memberships_table,
                users_table.c.uuid == service_memberships_table.c.user_uuid,
            )  # Join to service memberships
            .outerjoin(
                services_table,
                service_memberships_table.c.service_uuid == services_table.c.uuid,
            )  # Join to services
            .outerjoin(
                service_roles,
                service_memberships_table.c.role_id == service_roles.c.id,
            )
        )

        base_stmt = select(*columns_select).select_from(chain)

        # apply filters
        stmt = base_stmt.where(and_(*filters))

        # Sorting
        sort_option = {
            "created_at": users_table.c.created_at,
            "updated_at": users_table.c.updated_at,
        }

        stmt_order = sort_option.get(
            p.sort_by,
            users_table.c.created_at,
        )

        if p.sort_order == SortOrder.ASC:
            stmt = stmt.order_by(stmt_order.asc())
        elif p.sort_order == SortOrder.DESC:
            stmt = stmt.order_by(stmt_order.desc())
        else:
            stmt = stmt.order_by(stmt_order.desc())

        # Pagination
        offset = (p.page - 1) * p.limit
        stmt = stmt.offset(offset).limit(p.limit)

        # count query
        count_query = select(func.count()).select_from(chain).where(and_(*filters))

        return stmt, count_query


class AdminAsyncRepositories:
    @staticmethod
    def _extract_service_info(row: dict) -> dict:
        """Extract service information from a database row."""
        if not row["service_uuid"]:
            return None

        return {
            "uuid": row["service_uuid"],
            "name": row["service_name"],
            "description": row["service_description"],
            "role": row["service_role_name"],
            "service_is_active": row["service_is_active"],
            "member_is_active": row["member_is_active"],
        }

    @staticmethod
    @query_exceptions_handler
    async def get_user_details(
        role: str,
        user_uuid: UUID,
        connection: AsyncConnection,
    ) -> UserMembershipQueryReponse | None:
        stmt = AdminStatement.get_user_details(user_uuid=user_uuid, role=role)

        result = await connection.execute(stmt)
        row = result.mappings().all()

        if not row:
            return None

        services_member = []

        for r in row:
            # Extract service information from the row
            service_info = AdminAsyncRepositories._extract_service_info(r)
            if service_info:
                services_member.append(service_info)

        user_response = {
            **row,
            "services": services_member,
        }

        return UserMembershipQueryReponse(**dict(user_response))

    @staticmethod
    @query_exceptions_handler
    async def get_list_users(
        role: str,
        payload: GetUsersPayload,
        connection: AsyncConnection,
    ) -> tuple[list[UserMembershipQueryReponse] | None, MetaResponse | None]:
        stmt_data, stmt_count = AdminStatement.get_list_users(p=payload, role=role)

        # process data query
        result = await connection.execute(stmt_data)
        rows_raw = result.mappings().all()

        if not rows_raw:
            return None, None

        d_services = {}
        for row in rows_raw:
            services_member = []

            if row["service_uuid"] in d_services:
                d_services[row["uuid"]] = []

            service_info = AdminAsyncRepositories._extract_service_info(row)
            if service_info:
                d_services[row["uuid"]].append(service_info)

        ls_users = []
        for row in rows_raw:
            # Extract service information from the row
            services_member = d_services.get(row["uuid"], [])
            if not services_member:
                continue

            user_response = {
                **row,
                "services": services_member,
            }
            ls_users.append(user_response)

        rows = [UserMembershipQueryReponse(**dict(row)) for row in ls_users]

        # process metaresponse
        total_items_raw = await connection.execute(stmt_count)
        total_items = total_items_raw.scalar_one()
        total_pages = (total_items + payload.limit - 1) // payload.limit

        meta = {
            "current_page": payload.page,
            "page_size": len(rows),
            "prev_page": payload.page > 1,
            "next_page": payload.page < total_pages,
            "total_pages": total_pages,
            "total_items": total_items,
        }

        return rows, MetaResponse(**meta)
