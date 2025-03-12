"""Database connection dependencies module.

This module provides async connection managers for database operations,
including transaction support and simple read operations.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection
from src.helpers.database import engine_async


async def get_async_transaction_conn() -> AsyncGenerator[
    AsyncConnection,
    None,
]:
    """Asynchronously yields a SQLAlchemy AsyncConnection with transaction management.

    This dependency function provides an AsyncConnection within a transaction context.
    The transaction is automatically committed if the function using this connection
    completes successfully, or rolled back if an SQLAlchemyError occurs.

    Yields:
        AsyncConnection: An asynchronous SQLAlchemy connection object with an active transaction.

    Raises:
        SQLAlchemyError: If any database-related error occurs during the transaction.

    Example:
        ```
        @app.get("/example")
        async def example_endpoint(
            conn: AsyncConnection = Depends(get_async_transaction_conn),
        ):
            result = await conn.execute(select(User).where(User.id == 1))
            user = result.scalars().first()
            return {"user": user}
        ```

    """  # noqa: E501
    # Get async connection
    async with engine_async.connect() as connection:  # noqa: SIM117
        # Begin transaction
        async with connection.begin():
            try:
                yield connection
                # Transaction will be automatically committed
                # if no exceptions occur (feature of sqlalchemy2)
            except SQLAlchemyError as e:
                # Transaction will be automatically rolled back on exception
                print(f"SQLAlchemyError: {e}")
                raise
            finally:
                pass
                # Connection will be automatically closed due to async with


async def get_async_conn() -> AsyncGenerator[AsyncConnection, None]:
    """For simple read operations."""
    async with engine_async.connect() as connection:
        try:
            yield connection
        except SQLAlchemyError as e:
            print(f"SQLAlchemyError: {e}")
            raise
        finally:
            pass
