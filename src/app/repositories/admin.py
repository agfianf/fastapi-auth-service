from sqlalchemy import Select, Update, and_, delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection
from uuid_utils.compat import UUID

from app.helpers.error_database import query_exceptions_handler
from app.helpers.response_api import MetaResponse
from app.models.business_roles import business_roles_table
from app.models.roles import roles_table
from app.models.services import service_memberships_table, services_table
from app.models.users import users_table
from app.schemas.users.admin.payload import GetUsersPayload, SortOrder, UpdateUserByAdminPayload
from app.schemas.users.query import UserMembershipQueryReponse


class AdminStatement:
    @staticmethod
    def get_user_details(user_uuid: UUID, role: str):
        service_roles = business_roles_table.alias("service_roles")
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
                service_memberships_table.c.business_role_id == service_roles.c.id,
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
    def get_list_users_base(p: GetUsersPayload, role: str) -> tuple[Select, Select]:
        """Generate query untuk mendapatkan data user dasar."""
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
            users_table.c.created_by,
            users_table.c.updated_by,
            users_table.c.deleted_by,
            roles_table.c.name.label("role"),
        ]

        chain = users_table.outerjoin(roles_table, users_table.c.role_id == roles_table.c.id)

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

    @staticmethod
    def get_user_services(user_uuids: list[UUID]) -> Select:
        """Generate query untuk mendapatkan data service untuk user tertentu."""
        service_roles = roles_table.alias("service_roles")

        columns_select = [
            service_memberships_table.c.user_uuid,
            services_table.c.uuid.label("service_uuid"),
            services_table.c.name.label("service_name"),
            services_table.c.description.label("service_description"),
            services_table.c.is_active.label("service_is_active"),
            service_memberships_table.c.is_active.label("member_is_active"),
            service_roles.c.name.label("service_role_name"),
        ]

        chain = service_memberships_table.outerjoin(
            services_table,
            service_memberships_table.c.service_uuid == services_table.c.uuid,
        ).outerjoin(
            service_roles,
            service_memberships_table.c.business_role_id == service_roles.c.id,
        )

        stmt = select(*columns_select).select_from(chain).where(service_memberships_table.c.user_uuid.in_(user_uuids))

        return stmt

    @staticmethod
    def get_role_id(role_name: str) -> Select:
        """Generate query untuk mendapatkan role_id user."""
        stmt = select(roles_table.c.id).where(roles_table.c.name == role_name)
        return stmt

    @staticmethod
    def update_user_details(
        role_admin: str,
        user_uuid: UUID,
        executed_by: str,
        role_id_user: int | None,
        is_active: bool | None,
    ) -> Update:
        """Generate query untuk update user details."""
        filters = []
        if role_admin == "admin":
            # hide superadmin info from admin
            filters.append(users_table.c.role_id != 1)

        filters.append(users_table.c.deleted_at.is_(None))
        filters.append(users_table.c.uuid == user_uuid)

        update_values = {}
        if role_id_user is not None:
            update_values["role_id"] = role_id_user
        if is_active is not None:
            update_values["is_active"] = is_active
        update_values["updated_by"] = executed_by

        update_stmt = update(users_table).values(**update_values).where(and_(*filters)).returning(1)
        return update_stmt

    @staticmethod
    def hard_delete_user(
        role_admin: str,
        user_uuid: UUID,
    ) -> Update:
        """Generate query untuk delete user."""
        filters = []
        if role_admin == "admin":
            # hide superadmin info from admin
            filters.append(users_table.c.role_id != 1)

        filters.append(users_table.c.deleted_at.is_(None))
        filters.append(users_table.c.uuid == user_uuid)

        delete_stmt = delete(users_table).where(and_(*filters)).returning(1)
        return delete_stmt

    @staticmethod
    def soft_delete_user(
        role_admin: str,
        executed_by: str,
        user_uuid: UUID,
    ) -> Update:
        """Generate query untuk soft delete user."""
        filters = []
        if role_admin == "admin":
            # hide superadmin info from admin
            filters.append(users_table.c.role_id != 1)

        filters.append(users_table.c.deleted_at.is_(None))
        filters.append(users_table.c.uuid == user_uuid)

        update_stmt = (
            update(users_table)
            .values(
                deleted_at=func.now(),
                deleted_by=executed_by,
                is_active=False,
                mfa_enabled=False,
                mfa_secret=None,
            )
            .where(and_(*filters))
            .returning(1)
        )
        return update_stmt

    @staticmethod
    def delete_user_service_mappings(user_uuid: UUID) -> delete:
        """Generate query to delete existing service mappings for a user."""
        stmt = delete(service_memberships_table).where(service_memberships_table.c.user_uuid == user_uuid)
        return stmt

    @staticmethod
    def insert_user_service_mappings(mappings: list[dict]) -> insert:
        """Generate query to insert new service mappings for a user."""
        stmt = insert(service_memberships_table).values(mappings)
        return stmt


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
        rows = result.mappings().all()

        if not rows:
            return None

        services_member = []

        for row in rows:
            # Extract service information from the row
            service_info = AdminAsyncRepositories._extract_service_info(row)
            if service_info:
                services_member.append(service_info)

        user_response = {
            **rows[0],
            "services": services_member,
        }

        return UserMembershipQueryReponse(**user_response)

    @staticmethod
    @query_exceptions_handler
    async def get_list_users(
        role: str,
        payload: GetUsersPayload,
        connection: AsyncConnection,
    ) -> tuple[list[UserMembershipQueryReponse] | None, MetaResponse | None]:
        # 1. get data user dasar
        user_stmt, count_stmt = AdminStatement.get_list_users_base(p=payload, role=role)

        # Eksekusi query user
        user_result = await connection.execute(user_stmt)
        user_rows = user_result.mappings().all()

        if not user_rows:
            return None, None

        # 2. get UUID semua user untuk query service
        user_uuids = [row["uuid"] for row in user_rows]

        # 3. Query untuk mendapatkan service untuk user-user tersebut
        service_stmt = AdminStatement.get_user_services(user_uuids)

        # Eksekusi query service
        service_result = await connection.execute(service_stmt)
        service_rows = service_result.mappings().all()

        # 4. group service berdasarkan user_uuid
        user_services = {}
        for row in service_rows:
            user_uuid = row["user_uuid"]
            if user_uuid not in user_services:
                user_services[user_uuid] = []

            service_info = {
                "uuid": row["service_uuid"],
                "name": row["service_name"],
                "description": row["service_description"],
                "role": row["service_role_name"],
                "service_is_active": row["service_is_active"],
                "member_is_active": row["member_is_active"],
            }
            user_services[user_uuid].append(service_info)

        # 5. Merge user dengan service-nya
        users = []
        for user_row in user_rows:
            user_uuid = user_row["uuid"]
            user_data = dict(user_row)
            user_data["services"] = user_services.get(user_uuid, [])
            users.append(UserMembershipQueryReponse(**user_data))

        # 6. Hitung total untuk meta
        total_items_raw = await connection.execute(count_stmt)
        total_items = total_items_raw.scalar_one()
        total_pages = (total_items + payload.limit - 1) // payload.limit

        meta = MetaResponse(
            current_page=payload.page,
            page_size=len(users),
            prev_page=payload.page > 1,
            next_page=payload.page < total_pages,
            total_pages=total_pages,
            total_items=total_items,
        )

        return users, meta

    @staticmethod
    @query_exceptions_handler
    async def update_user_details(
        role_admin: str,
        user_uuid: UUID,
        executed_by: str,
        payload: UpdateUserByAdminPayload,
        connection: AsyncConnection,
    ) -> bool:
        # get role_id
        role_id_user = None
        if payload.role is not None:
            role_stmt = AdminStatement.get_role_id(role_name=payload.role)
            role_result = await connection.execute(role_stmt)
            role_id_user = role_result.scalar_one_or_none()

        # update user
        update_stmt = AdminStatement.update_user_details(
            role_admin=role_admin,
            user_uuid=user_uuid,
            executed_by=executed_by,
            role_id_user=role_id_user,
            is_active=payload.is_active,
        )
        result_update = await connection.execute(update_stmt)
        return result_update.scalar_one_or_none() == 1

    @staticmethod
    @query_exceptions_handler
    async def soft_delete_user(
        role_admin: str,
        executed_by: str,
        user_uuid: UUID,
        connection: AsyncConnection,
    ) -> bool:
        """Delete user."""
        delete_stmt = AdminStatement.soft_delete_user(
            role_admin=role_admin,
            user_uuid=user_uuid,
            executed_by=executed_by,
        )

        result = await connection.execute(delete_stmt)
        return result.scalar_one_or_none() == 1

    @staticmethod
    @query_exceptions_handler
    async def update_user_services(
        role_admin: str,  # noqa: ARG004
        executed_by: str,
        user_uuid: UUID,
        services: list,
        connection: AsyncConnection,
    ) -> bool:
        """Update user service mappings."""
        # First, delete all existing mappings for this user
        delete_stmt = AdminStatement.delete_user_service_mappings(user_uuid=user_uuid)
        await connection.execute(delete_stmt)

        # Then insert the new mappings if any are provided
        if services:
            values = []
            for service in services:
                values.append(
                    {
                        "user_uuid": user_uuid,
                        "service_uuid": service.service_uuid,
                        "business_role_id": service.business_role_id,
                        "is_active": service.is_active,
                        "created_by": executed_by,
                        "updated_by": executed_by,
                    }
                )

            insert_stmt = AdminStatement.insert_user_service_mappings(mappings=values)
            await connection.execute(insert_stmt)

        return True
