from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.helpers.response_api import JsonResponse


async def handle_error_response(
    request: Request,  # noqa: ARG001
    exc: HTTPException | RequestValidationError,
) -> JSONResponse:
    """Handle both HTTP exceptions and validation errors.

    Parameters
    ----------
    request : Request
        The request that caused the exception
    exc : Union[HTTPException, RequestValidationError]
        The exception that was raised

    Returns
    -------
    JSONResponse
        A formatted JSON response containing error details

    """
    # Handle HTTPException
    if isinstance(exc, HTTPException):
        msg = exc.detail
        status_code = exc.status_code

        if status_code < 200 or status_code >= 300:
            data = JsonResponse(
                data=None,
                message=msg,
                status_code=status_code,
                success=False,
            )
            return JSONResponse(
                content=data.model_dump(),
                status_code=status_code,
            )

    # Handle RequestValidationError
    elif isinstance(exc, RequestValidationError):
        errors = exc.errors()
    
        if errors:
            type_error = errors[0]["type"]
            location = " in ".join(str(item) for item in errors[0]["loc"])
            msg_error = errors[0]["msg"]
            pesan = f"Invalid input. Please check and try again. {type_error=} | {location=}. {msg_error=}"
        else:
            pesan = "Invalid input. Please check and try again."

        data = JsonResponse(
            data=None,
            message=pesan,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            success=False,
        )
        return JSONResponse(
            content=data.model_dump(),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    # Handle any other exceptions with a generic 500 error
    data = JsonResponse(
        data=None,
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        success=False,
    )
    return JSONResponse(
        content=data.model_dump(),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
