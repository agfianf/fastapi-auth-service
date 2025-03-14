from sqlalchemy import Insert, insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.helpers.error_database import query_exceptions_handler
from app.models.users import users_table
from app.schemas.users import CreateUserQuery, CreateUserQueryResponse


class AuthStatements:
    @staticmethod
    def create_user(payload: CreateUserQuery) -> Insert:
        return insert(users_table).values(**payload.transform()).returning(*users_table.c)


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
