import traceback

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError

from app.exceptions.database import (
    DataAlreadyExistsException,
    DatabaseException,
    DataDuplicateException,
    DataNotFoundException,
    DataNotNullException,
    DataOperationException,
)


T = TypeVar("T")
P = ParamSpec("P")  # Parameter types


def query_exceptions_handler(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    """Handle database exceptions in async functions.

    Parameters
    ----------
    func : Callable
        The async function to be decorated

    Returns
    -------
    Callable
        Wrapped function with exception handling

    Raises
    ------
    HTTPException
        With appropriate status code depending on the exception type

    """

    @wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return await func(*args, **kwargs)

        except NoResultFound as e:
            error_details = f"Data not found: {str(e)}"
            print(f"NoResultFound: {error_details}")
            print(f"Traceback: {traceback.format_exc()}")
            raise DataNotFoundException(detail=error_details) from e

        except IntegrityError as e:
            error_trace = traceback.format_exc()
            error_msg = str(e)
            print(f"Database integrity error: {error_msg}\n{error_trace}")

            if "duplicate key" in error_msg:
                raise DataDuplicateException(detail=f"{e}") from e

            if "null value in column" in error_msg:
                raise DataNotNullException(detail=f"{e}") from e

            raise DataAlreadyExistsException(detail=f"{e}") from e

        except SQLAlchemyError as e:
            error_trace = traceback.format_exc()
            error_msg = str(e)
            print(f"Database error: {error_msg}\n{error_trace}")
            raise DataOperationException(f"{e}") from e

        except Exception as e:
            error_trace = traceback.format_exc()
            error_msg = str(e)
            print(f"Unexpected database error: {error_msg}\n{error_trace}")
            raise DatabaseException(f"{error_msg}") from e

    return async_wrapper
