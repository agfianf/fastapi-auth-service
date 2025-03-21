from fastapi import HTTPException, status


class MemberNotFoundException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )


class MemberUpdateException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update member information",
        )


class PasswordUpdateFailedException(HTTPException):
    def __init__(self, messages: list[str] | None = None) -> None:
        if messages:
            err_msg = ", ".join(messages)
            full_message = f"Failed to update password. {err_msg}"
        else:
            full_message = "Failed to update password."

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=full_message,
        )


class InvalidCurrentPasswordException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )


class MFAUpdateFailedException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update MFA settings",
        )


class MFANotEnabledException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not yet enabled for this account",
        )


class MFACodeInvalidException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA code provided",
        )
