import traceback

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError


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

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_details,
            ) from e

        except IntegrityError as e:
            error_trace = traceback.format_exc()
            error_msg = str(e)
            print(f"Database integrity error: {error_msg}\n{error_trace}")

            if "duplicate key" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Resource already exists or registered.",
                ) from e

            if "null value in column" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Please fill in all required fields.",
                ) from e

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Resource already exists or constraint violation.",
            ) from e

        except SQLAlchemyError as e:
            error_trace = traceback.format_exc()
            error_msg = str(e)
            print(f"Database error: {error_msg}\n{error_trace}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed.",
            ) from e

        except Exception as e:
            error_trace = traceback.format_exc()
            error_msg = str(e)
            print(f"Unexpected database error: {error_msg}\n{error_trace}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected database error occurred.",
            ) from e

    return async_wrapper
