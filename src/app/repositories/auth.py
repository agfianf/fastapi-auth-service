from sqlalchemy import Insert, and_, insert, select
from sqlalchemy.ext.asyncio import AsyncConnection

from app.helpers.error_database import query_exceptions_handler
from app.models.roles import roles_table
from app.models.services import service_memberships_table, services_table
from app.models.users import users_table
from app.schemas.users import CreateUserQuery, CreateUserQueryResponse
from app.schemas.users.query import UserMembershipQueryReponse


class AuthStatements:
    @staticmethod
    def create_user(payload: CreateUserQuery) -> Insert:
        return insert(users_table).values(**payload.transform()).returning(*users_table.c)

    @staticmethod
    def get_user_by_username(username: str) -> select:
        # Join with roles, service_memberships, services, and roles for service memberships
        stmt = (
            select(
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
                roles_table.c.name.label("role_name"),  # Main role name from users.role_id
                services_table.c.uuid.label("service_uuid"),
                services_table.c.name.label("service_name"),
                services_table.c.description.label("service_description"),
                services_table.c.is_active.label("service_is_active"),
                service_memberships_table.c.is_active.label("member_is_active"),
                roles_table.c.name.label("service_role_name"),  # Role name from service_memberships
            )
            .select_from(users_table)
            .outerjoin(roles_table, users_table.c.role_id == roles_table.c.id)  # Main role
            .outerjoin(
                service_memberships_table,
                users_table.c.uuid == service_memberships_table.c.user_uuid,
            )  # Join to service memberships
            .outerjoin(
                services_table,
                service_memberships_table.c.service_uuid == services_table.c.uuid,
            )  # Join to services
            .outerjoin(
                roles_table.alias("service_roles"),
                service_memberships_table.c.role_id == roles_table.alias("service_roles").c.id,
            )  # Join to roles for service memberships
            .where(
                and_(
                    users_table.c.username == username,
                    users_table.c.deleted_at.is_(None),
                    service_memberships_table.c.deleted_at.is_(None),
                    services_table.c.deleted_at.is_(None),
                )
            )
        )

        return stmt


class AuthAsyncRepositories:
    @staticmethod
    @query_exceptions_handler
    async def create_user(
        connection: AsyncConnection,
        payload: CreateUserQuery,
    ) -> CreateUserQueryResponse:
        stmt = AuthStatements.create_user(payload=payload)
        result = await connection.execute(stmt)
        new_user = result.mappings().first()
        return CreateUserQueryResponse.model_validate(dict(new_user))

    @staticmethod
    @query_exceptions_handler
    async def get_user_by_username(
        connection: AsyncConnection,
        username: str,
    ) -> UserMembershipQueryReponse | None:
        stmt = AuthStatements.get_user_by_username(username=username)
        result = await connection.execute(stmt)
        rows = result.mappings().all()
        print(rows)

        if not rows:
            return None

        user_data = dict(rows[0])
        services = []

        for row in rows:
            if row["service_uuid"]:
                service = {
                    "uuid": row["service_uuid"],
                    "name": row["service_name"],
                    "description": row["service_description"],
                    "role": row["service_role_name"],
                    "service_is_active": row["service_is_active"],
                    "member_is_active": row["member_is_active"],
                }
                services.append(service)

        user_response = {
            **user_data,
            "services": services,
        }
        return UserMembershipQueryReponse.model_validate(user_response)
