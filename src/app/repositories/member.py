from sqlalchemy import Update, and_, select, update
from sqlalchemy.ext.asyncio import AsyncConnection
from uuid_utils.compat import UUID

from app.helpers.error_database import query_exceptions_handler
from app.models.roles import roles_table
from app.models.services import service_memberships_table, services_table
from app.models.users import users_table
from app.schemas.member.payload import UpdateMemberPayload
from app.schemas.users.query import UserMembershipQueryReponse


class MemberStatements:
    @staticmethod
    def get_member_by_uuid(member_uuid: UUID):
        """Generate query to get member by UUID."""
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
            roles_table.c.id.label("role_id"),
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
            )
            .outerjoin(
                services_table,
                service_memberships_table.c.service_uuid == services_table.c.uuid,
            )
            .outerjoin(
                service_roles,
                service_memberships_table.c.role_id == service_roles.c.id,
            )
        )

        filters = [
            users_table.c.deleted_at.is_(None),
            users_table.c.uuid == member_uuid,
        ]

        stmt = select(*columns_select).select_from(chain).where(and_(*filters))

        return stmt

    @staticmethod
    def update_member_password(member_uuid: UUID, password_hash: str, executed_by: str) -> Update:
        """Generate query to update member password."""
        stmt = (
            update(users_table)
            .where(
                and_(
                    users_table.c.uuid == member_uuid,
                    users_table.c.deleted_at.is_(None),
                )
            )
            .values(
                password_hash=password_hash,
                updated_by=executed_by,
            )
            .returning(*users_table.c)
        )
        return stmt

    @staticmethod
    def update_member_mfa(member_uuid: UUID, mfa_enabled: bool, mfa_secret: str | None, executed_by: str) -> Update:
        """Generate query to update member MFA settings."""
        update_values = {
            "mfa_enabled": mfa_enabled,
            "updated_by": executed_by,
        }

        if mfa_secret is not None:
            update_values["mfa_secret"] = mfa_secret
        elif not mfa_enabled:
            update_values["mfa_secret"] = None

        stmt = (
            update(users_table)
            .where(
                and_(
                    users_table.c.uuid == member_uuid,
                    users_table.c.deleted_at.is_(None),
                )
            )
            .values(**update_values)
            .returning(*users_table.c)
        )
        return stmt

    @staticmethod
    def update_member_profile(member_uuid: UUID, payload: dict, executed_by: str) -> Update:
        """Generate query to update member profile."""
        update_values = payload.copy()
        update_values["updated_by"] = executed_by

        stmt = (
            update(users_table)
            .where(
                and_(
                    users_table.c.uuid == member_uuid,
                    users_table.c.deleted_at.is_(None),
                )
            )
            .values(**update_values)
            .returning(*users_table.c)
        )
        return stmt


class MemberAsyncRepositories:
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
    async def get_member_by_uuid(
        connection: AsyncConnection,
        member_uuid: UUID,
    ) -> UserMembershipQueryReponse | None:
        """Get member by UUID."""
        stmt = MemberStatements.get_member_by_uuid(member_uuid=member_uuid)
        result = await connection.execute(stmt)
        rows = result.mappings().all()

        if not rows:
            return None

        services_member = []

        for row in rows:
            # Extract service information from the row
            service_info = MemberAsyncRepositories._extract_service_info(row)
            if service_info:
                services_member.append(service_info)

        user_response = {
            **rows[0],
            "services": services_member,
        }

        return UserMembershipQueryReponse.model_validate(user_response)

    @staticmethod
    @query_exceptions_handler
    async def update_member_password(
        connection: AsyncConnection,
        member_uuid: UUID,
        password_hash: str,
        executed_by: str,
    ) -> bool:
        """Update member password."""
        stmt = MemberStatements.update_member_password(
            member_uuid=member_uuid,
            password_hash=password_hash,
            executed_by=executed_by,
        )
        result = await connection.execute(stmt)
        return result.rowcount > 0

    @staticmethod
    @query_exceptions_handler
    async def update_member_mfa(
        connection: AsyncConnection,
        member_uuid: UUID,
        mfa_enabled: bool,
        mfa_secret: str | None,
        executed_by: str,
    ) -> bool:
        """Update member MFA settings."""
        stmt = MemberStatements.update_member_mfa(
            member_uuid=member_uuid,
            mfa_enabled=mfa_enabled,
            mfa_secret=mfa_secret,
            executed_by=executed_by,
        )
        result = await connection.execute(stmt)
        return result.rowcount > 0

    @staticmethod
    @query_exceptions_handler
    async def update_member_profile(
        connection: AsyncConnection,
        member_uuid: UUID,
        payload: UpdateMemberPayload,
        executed_by: str,
    ) -> UserMembershipQueryReponse | None:
        """Update member profile."""
        update_data = payload.transform()
        if not update_data:
            # If there's nothing to update, return the current member
            return await MemberAsyncRepositories.get_member_by_uuid(
                connection=connection,
                member_uuid=member_uuid,
            )

        stmt = MemberStatements.update_member_profile(
            member_uuid=member_uuid,
            payload=update_data,
            executed_by=executed_by,
        )
        result = await connection.execute(stmt)
        updated_row = result.mappings().first()

        if not updated_row:
            return None

        # Fetch the complete updated member with services
        return await MemberAsyncRepositories.get_member_by_uuid(
            connection=connection,
            member_uuid=member_uuid,
        )
